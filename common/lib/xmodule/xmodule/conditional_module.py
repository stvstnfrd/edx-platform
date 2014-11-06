"""Conditional module is the xmodule, which you can use for disabling
some xmodules by conditions.
"""

import json
import logging
from lazy import lazy
from lxml import etree
from pkg_resources import resource_string
from uuid import uuid4

from xmodule.x_module import XModule, STUDENT_VIEW
from xmodule.seq_module import SequenceDescriptor
from xblock.fields import Scope, ReferenceList
from xmodule.modulestore.exceptions import ItemNotFoundError


log = logging.getLogger('edx.' + __name__)
_ = lambda x: x
DEFAULT_CONDITION_NAME = _(u'Conditional ({condition})')


class ConditionalFields(object):
    has_children = True
    show_tag_list = ReferenceList(help="List of urls of children that are references to external modules", scope=Scope.content)
    sources_list = ReferenceList(help="List of sources upon which this module is conditional", scope=Scope.content)


class ConditionalModule(ConditionalFields, XModule):
    """
    Blocks child module from showing unless certain conditions are met.

    Example:

        <conditional sources="i4x://.../problem_1; i4x://.../problem_2" completed="True">
            <show sources="i4x://.../test_6; i4x://.../Avi_resources"/>
            <video url_name="secret_video" />
        </conditional>

        <conditional> tag attributes:
            sources - location id of required modules, separated by ';'

            submitted - map to `is_submitted` module method.
            (pressing RESET button makes this function to return False.)

            attempted - map to `is_attempted` module method
            correct - map to `is_correct` module method
            poll_answer - map to `poll_answer` module attribute
            voted - map to `voted` module attribute

        <show> tag attributes:
            sources - location id of required modules, separated by ';'

        You can add you own rules for <conditional> tag, like
        "completed", "attempted" etc. To do that yo must extend
        `ConditionalModule.conditions_map` variable and add pair:
            my_attr: my_property/my_method

        After that you can use it:
            <conditional my_attr="some value" ...>
                ...
            </conditional>

        And my_property/my_method will be called for required modules.

    """

    js = {
        'coffee': [
            resource_string(__name__, 'js/src/javascript_loader.coffee'),
            resource_string(__name__, 'js/src/conditional/display.coffee'),
        ],
        'js': [
            resource_string(__name__, 'js/src/collapsible.js'),
        ]
    }

    js_module_name = "Conditional"
    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}

    # Map
    # key: <tag attribute in xml>
    # value: <name of module attribute>
    conditions_map = {
        'poll_answer': 'poll_answer',  # poll_question attr

        # problem was submitted (it can be wrong)
        # if student will press reset button after that,
        # state will be reverted
        'submitted': 'is_submitted',  # capa_problem attr

        # if student attempted problem
        'attempted': 'is_attempted',  # capa_problem attr

        # if problem is full points
        'correct': 'is_correct',

        'voted': 'voted'  # poll_question attr
    }

    def _get_condition(self):
        # Get first valid condition.
        # from xmodule.modulestore.django import modulestore
        # course = modulestore().get_course(self.location.course_key)
        # print(self.location.course_key, course)
        for xml_attr, attr_name in self.conditions_map.iteritems():
            xml_value = self.descriptor.xml_attributes.get(xml_attr)
            if xml_value:
                return xml_value, attr_name
        return None, None
        raise Exception(
            'Error in conditional module: no known conditional found in {!r}'.format(
                self.descriptor.xml_attributes.keys()
            )
        )

    @lazy
    def required_modules(self):
        return [self.system.get_module(descriptor) for
                descriptor in self.descriptor.get_required_module_descriptors()]

    def is_condition_satisfied(self):
        xml_value, attr_name = self._get_condition()

        if xml_value and self.required_modules:
            for module in self.required_modules:
                if not hasattr(module, attr_name):
                    # We don't throw an exception here because it is possible for
                    # the descriptor of a required module to have a property but
                    # for the resulting module to be a (flavor of) ErrorModule.
                    # So just log and return false.
                    log.warn('Error in conditional module: \
                        required module {module} has no {module_attr}'.format(module=module, module_attr=attr_name))
                    return False

                attr = getattr(module, attr_name)
                if callable(attr):
                    attr = attr()

                if xml_value != str(attr):
                    break
            else:
                return True
        return False

    def get_html(self):
        # Calculate html ids of dependencies
        self.required_html_ids = [descriptor.location.html_id() for
                                  descriptor in self.descriptor.get_required_module_descriptors()]

        return self.system.render_template('conditional_ajax.html', {
            'element_id': self.location.html_id(),
            'ajax_url': self.system.ajax_url,
            'depends': ';'.join(self.required_html_ids)
        })

    def handle_ajax(self, _dispatch, _data):
        """This is called by courseware.moduleodule_render, to handle
        an AJAX call.
        """
        if not self.is_condition_satisfied():
            defmsg = "{link} must be attempted before this will become visible."
            message = self.descriptor.xml_attributes.get('message', defmsg)
            context = {'xmodule': self,
                       'message': message}
            html = self.system.render_template('conditional_module.html',
                                               context)
            return json.dumps({'html': [html], 'message': bool(message)})

        html = [child.render(STUDENT_VIEW).content for child in self.get_display_items()]

        return json.dumps({'html': html})

    def get_icon_class(self):
        new_class = 'other'
        # HACK: This shouldn't be hard-coded to two types
        # OBSOLETE: This obsoletes 'type'
        class_priority = ['video', 'problem']

        child_classes = [self.system.get_module(child_descriptor).get_icon_class()
                         for child_descriptor in self.descriptor.get_children()]
        for c in class_priority:
            if c in child_classes:
                new_class = c
        return new_class

    def studio_render_children(self, fragment, children, context):
        """
        Renders the specified children and returns it as an HTML string. In addition, any
        dependencies are added to the specified fragment.
        """
        html = ""
        for active_child_descriptor in children:
            active_child = self.system.get_module(active_child_descriptor)
            rendered_child = active_child.render(StudioEditableModule.get_preview_view_name(active_child), context)
            if active_child.category == 'vertical':
                group_name, group_id  = self.get_data_for_vertical(active_child)
                if group_name:
                    rendered_child.content = rendered_child.content.replace(
                        DEFAULT_GROUP_NAME.format(group_id=group_id),
                        group_name
                    )
            fragment.add_frag_resources(rendered_child)
            html = html + rendered_child.content

        return html

    def author_view(self, context):
        """
        Renders the Studio preview by rendering each child so that they can all be seen and edited.
        """
        print('UGGGHGHGHGHGHGHGHGHGHGHGHGHGHGHGH')
        fragment = Fragment()
        root_xblock = context.get('root_xblock')
        is_configured = False # not self.user_partition_id == SplitTestFields.no_partition_selected['value']
        is_root = root_xblock and root_xblock.location == self.location
        active_groups_preview = None
        # inactive_groups_preview = None

        if is_root:
            [active_children, inactive_children] = self.descriptor.active_and_inactive_children()
            active_groups_preview = self.studio_render_children(
                fragment, active_children, context
            )
            # inactive_groups_preview = self.studio_render_children(
            #     fragment, inactive_children, context
            # )

        fragment.add_content(self.system.render_template('conditional_author_view.html', {
            'split_test': self,
            'is_root': is_root,
            'is_configured': is_configured,
            'active_groups_preview': active_groups_preview,
            # 'inactive_groups_preview': inactive_groups_preview,
            'group_configuration_url': self.descriptor.group_configuration_url,
        }))
        # fragment.add_javascript_url(self.runtime.local_resource_url(self, 'public/js/split_test_author_view.js'))
        fragment.initialize_js('(function () { alert("hi"); })')

        return fragment

    def student_view(self, context):
        if self.system.user_is_staff:
            return self.staf


class ConditionalDescriptor(ConditionalFields, SequenceDescriptor):
    """Descriptor for conditional xmodule."""
    _tag_name = 'conditional'

    module_class = ConditionalModule

    filename_extension = "xml"

    has_score = False

    def __init__(self, *args, **kwargs):
        """
        Create an instance of the conditional module.
        """
        super(ConditionalDescriptor, self).__init__(*args, **kwargs)
        # Convert sources xml_attribute to a ReferenceList field type so Location/Locator
        # substitution can be done.
        print('FUNK', len(self.children), self.children)
        if not self.children:
            self.add_default_verticals()
        if not self.sources_list:
            if 'sources' in self.xml_attributes and isinstance(self.xml_attributes['sources'], basestring):
                self.sources_list = [
                    self.location.course_key.make_usage_key_from_deprecated_string(item)
                    for item in ConditionalDescriptor.parse_sources(self.xml_attributes)
                ]

    @staticmethod
    def parse_sources(xml_element):
        """ Parse xml_element 'sources' attr and return a list of location strings. """
        sources = xml_element.get('sources')
        if sources:
            return [location.strip() for location in sources.split(';')]

    def get_required_module_descriptors(self):
        """Returns a list of XModuleDescriptor instances upon
        which this module depends.
        """
        descriptors = []
        for location in self.sources_list:
            try:
                descriptor = self.system.load_item(location)
                descriptors.append(descriptor)
            except ItemNotFoundError:
                msg = "Invalid module by location."
                log.exception(msg)
                self.system.error_tracker(msg)

        return descriptors

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        show_tag_list = []
        for child in xml_object:
            if child.tag == 'show':
                locations = ConditionalDescriptor.parse_sources(child)
                for location in locations:
                    children.append(location)
                    show_tag_list.append(location)
            else:
                try:
                    descriptor = system.process_xml(etree.tostring(child))
                    children.append(descriptor.scope_ids.usage_id)
                except:
                    msg = "Unable to load child when parsing Conditional."
                    log.exception(msg)
                    system.error_tracker(msg)
        return {'show_tag_list': show_tag_list}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element(self._tag_name)
        for child in self.get_children():
            if child.location not in self.show_tag_list:
                self.runtime.add_block_as_child_node(child, xml_object)

        if self.show_tag_list:
            show_str = u'<{tag_name} sources="{sources}" />'.format(
                tag_name='show', sources=';'.join(location.to_deprecated_string() for location in self.show_tag_list))
            xml_object.append(etree.fromstring(show_str))

        # Overwrite the original sources attribute with the value from sources_list, as
        # Locations may have been changed to Locators.
        stringified_sources_list = map(lambda loc: loc.to_deprecated_string(), self.sources_list)
        self.xml_attributes['sources'] = ';'.join(stringified_sources_list)
        return xml_object

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(ConditionalDescriptor, self).non_editable_metadata_fields
        non_editable_fields.extend([
            ConditionalDescriptor.due,
        ])
        return non_editable_fields

    @property
    def editable_metadata_fields(self):
        editable_fields = super(ConditionalDescriptor, self).editable_metadata_fields

        # Explicitly add user_partition_id, which does not automatically get picked up because it is Scope.content.
        # Note that this means it will be saved by the Studio editor as "metadata", but the field will
        # still update correctly.
        # editable_fields[ConditionalDescriptor.sources_list.name] = ConditionalDescriptor.sources_list

        return editable_fields

    def add_default_verticals(self):
        user_id = self.runtime.user_id
        for condition in [True, False]:
            self._create_vertical_for_group(condition, user_id)

    # TODO: This is ripped from split_test_module.py
    # This logic will need reconciled and reworked/combined.
    def _create_vertical_for_group(self, condition, user_id):
        """
        Creates a vertical to associate with the group.

        This appends the new vertical to the end of children, and updates group_id_to_child.
        A mutable modulestore is needed to call this method (will need to update after mixed
        modulestore work, currently relies on mongo's create_item method).
        """
        assert hasattr(self.system, 'modulestore') and hasattr(self.system.modulestore, 'create_item'), \
            "editor_saved should only be called when a mutable modulestore is available"
        modulestore = self.system.modulestore
        dest_usage_key = self.location.replace(category="vertical", name=uuid4().hex)
        # metadata = {'display_name': DEFAULT_GROUP_NAME.format(group_id=group.id)}
        metadata = {'display_name': _(u'Conditional ({condition})').format(condition=condition)}
        modulestore.create_item(
            user_id,
            self.location.course_key,
            dest_usage_key.block_type,
            block_id=dest_usage_key.block_id,
            definition_data=None,
            metadata=metadata,
            runtime=self.system,
        )
        self.children.append(dest_usage_key)  # pylint: disable=no-member
        # self.group_id_to_child[unicode(group.id)] = dest_usage_key

    def editor_saved(self, user, old_metadata, old_content):
        print('STV SVD')

    # Ripped from split_test_module.py
    def has_dynamic_children(self):
        """
        Grading needs to know that only one of the children is actually "real".  This
        makes it use module.get_child_descriptors().
        """
        return True

    def validation_messages(self):
        messages = []
        if not len(self.children):
            messages.append(ValidationMessage(
                self,
                'wtf no kids!',
                ValidationMessageType.warning,
                'edit-button',
                'ACTION LABEL DO STUFF',
            ))
        return messages

    @property
    def general_validation_message(self):
        """
        Message for either error or warning validation message/s.

        Returns message and type. Priority given to error type message.
        """
        validation_messages = self.validation_messages()
        if validation_messages:
            has_error = any(message.message_type == ValidationMessageType.error for message in validation_messages)
            return {
                'message': _(u"This content experiment has issues that affect content visibility."),
                'type': ValidationMessageType.error if has_error else ValidationMessageType.warning,
            }
        return None


class ValidationMessageType(object):
    """
    The type for a validation message -- currently 'information', 'warning' or 'error'.
    """
    information = 'information'
    warning = 'warning'
    error = 'error'

    @staticmethod
    def display_name(message_type):
        """
        Returns the display name for the specified validation message type.
        """
        if message_type == ValidationMessageType.warning:
            # Translators: This message will be added to the front of messages of type warning,
            # e.g. "Warning: this component has not been configured yet".
            return _(u"Warning")
        elif message_type == ValidationMessageType.error:
            # Translators: This message will be added to the front of messages of type error,
            # e.g. "Error: required field is missing".
            return _(u"Error")
        else:
            return None


# TODO: move this into the xblock repo once it has a formal validation contract
class ValidationMessage(object):
    """
    Represents a single validation message for an xblock.
    """
    def __init__(self, xblock, message_text, message_type, action_class=None, action_label=None):
        assert isinstance(message_text, unicode)
        self.xblock = xblock
        self.message_text = message_text
        self.message_type = message_type
        self.action_class = action_class
        self.action_label = action_label

    def __unicode__(self):
        return self.message_text
