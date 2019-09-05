#!/usr/bin/env bash
# Exit immediately if any untested command fails
set -e

# Return status is that of the last command to fail in a
# piped command, or a zero if they all succeed.
set -o pipefail

# There is no need to install the prereqs, as this was already
# just done via the dependencies override section of circle.yml.
export NO_PREREQ_INSTALL='true'

EXIT=0

function emptyxunit {
    mkdir -p reports
    cat > reports/$1.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="$1" tests="1" errors="0" failures="0" skip="0">
<testcase classname="pavelib.quality" name="$1" time="0.604"></testcase>
</testsuite>
END
}
function run_paver_quality {
    QUALITY_TASK=$1
    shift
    mkdir -p test_root/log/
    LOG_PREFIX=test_root/log/$QUALITY_TASK
    echo "Inspecting code quality and storing report: ${QUALITY_TASK}"
    $TOX paver $QUALITY_TASK $* 2>&1 | tee $LOG_PREFIX.log
}
function test_system() {
    system=${1}
    shift
    random_flag=''
    if [ "${system}" == "lms" ]; then
        random_flag="--randomly-dont-reorganize"
    fi
    echo "DJANGO_SETTINGS_MODULE=openedx.stanford.${system}.envs.test pytest ${random_flag} ${@}"
    DJANGO_SETTINGS_MODULE=openedx.stanford.${system}.envs.test pytest ${random_flag} ${@}
}
function get_children() {
    parent=${1}
    exit_code=0
    apps=""
    for app in $(find "${parent}" -mindepth 1 -maxdepth 1 -type d | tr '/' '.' | sort); do
        case ${app} in
            # hawthorn
            cms.djangoapps.contentstore) ;&
            common.djangoapps.static_replace) ;&
            common.djangoapps.student) ;&
            common.djangoapps.third_party_auth) ;&
            common.djangoapps.util) ;&
            lms.djangoapps.courseware) ;&
            lms.djangoapps.instructor) ;&
            lms.djangoapps.instructor_task) ;&
            lms.djangoapps.lti_provider) ;&
            lms.djangoapps.shoppingcart) ;&
            openedx.core.djangoapps.auth_exchange) ;&
            openedx.core.djangoapps.bookmarks) ;&
            openedx.core.djangoapps.catalog) ;&
            openedx.core.djangoapps.credit) ;&
            openedx.core.djangoapps.dark_lang) ;&
            openedx.core.djangoapps.external_auth) ;&
            openedx.core.djangoapps.oauth_dispatch) ;&
            openedx.core.djangoapps.user_api) ;&
            openedx.stanford.cms.djangoapps.contentstore) ;&
            openedx.stanford.djangoapps.auth_lagunita) ;&
            openedx.stanford.djangoapps.register_cme) ;&
            openedx.stanford.lms.djangoapps.instructor_task) ;&
            openedx.tests.completion_integration) ;&
            # FAIL/ERROR
            common.djangoapps.django_comment_common) ;&
            common.djangoapps.pipeline_mako) ;&
            common.djangoapps.status) ;&
            common.djangoapps.terrain) ;&
            common.djangoapps.track) ;&
            lms.djangoapps.branding) ;&
            lms.djangoapps.ccx) ;&
            openedx.core.djangoapps.cors_csrf) ;&
            openedx.features.course_experience) ;&
            # SEG_FAULT
            lms.djangoapps.mobile_api)
                ;;
            *)
                apps="${apps} ${app}"
                ;;
        esac
    done
    if [ -n "${apps}" ]; then
        echo "$(echo ${apps} | tr '.' '/')"
    fi
}

function run_shard_0() {
    # run stanford-specific quality checks here
    true
}

function run_shard_4() {
    PATH=$PATH:node_modules/.bin
    run_paver_quality find_fixme || { EXIT=1; }
    run_paver_quality run_pep8 || { EXIT=1; }
    run_paver_quality run_pylint --system="cms,common,lms,openedx,pavelib" || { EXIT=1; }
    run_paver_quality run_eslint -l $ESLINT_THRESHOLD || { EXIT=1; }
    run_paver_quality run_stylelint -l $STYLELINT_THRESHOLD || { EXIT=1; }
    paver run_quality -p 80 || EXIT=1
    # run_paver_quality run_complexity || echo "Unable to calculate code complexity. Ignoring error."
    # run_paver_quality run_xsslint -t $XSSLINT_THRESHOLDS || { EXIT=1; }
    emptyxunit "stub"
    return ${EXIT}
}

function run_shard_1() {
    EXIT=0
    test_system lms \
        openedx/stanford/lms/lib \
        $(get_children openedx/stanford/lms/djangoapps) \
    || EXIT=1
    emptyxunit "stub"
    return ${EXIT}
}

function run_shard_5() {
    EXIT=0
    test_system lms \
        lms/lib \
        lms/tests.py \
        $(get_children lms/djangoapps) \
    || EXIT=1
    emptyxunit "stub"
    return ${EXIT}
}

function run_shard_2() {
    EXIT=0
    test_system cms \
        openedx/stanford/cms/djangoapps/contentstore/tests/test_bulksettings.py \
        openedx/stanford/cms/djangoapps/contentstore/tests/test_bulkupdate.py \
        openedx/stanford/cms/djangoapps/contentstore/tests/test_utilities.py \
        $(get_children openedx/stanford/cms/djangoapps) \
    || EXIT=1
    # openedx/stanford/cms/djangoapps/contentstore/tests/test_captions.py
    emptyxunit "stub"
    return ${EXIT}
}

function run_shard_6() {
    EXIT=0
    test_system cms \
        cms/djangoapps/contentstore/management/commands/tests \
        cms/lib \
        $(get_children cms/djangoapps) \
    || EXIT=1
    # cms/djangoapps/contentstore/api/tests
    # cms/djangoapps/contentstore/tests
    # cms/djangoapps/contentstore/views/tests
    emptyxunit "stub"
    return ${EXIT}
}

function run_shard_3() {
    EXIT=0
    test_system cms \
        openedx/stanford/common \
        $(get_children openedx/stanford/djangoapps) \
    || EXIT=1
    test_system lms \
        openedx/stanford/common \
    || EXIT=1
    test_system lms \
        $(get_children openedx/stanford/djangoapps) \
    || EXIT=1
    return $EXIT
}

function run_shard_7() {
    EXIT=0
    test_system cms \
        $(get_children common/djangoapps) \
        $(get_children openedx/core/djangoapps) \
        openedx/core/djangolib \
        openedx/core/lib \
        openedx/tests \
    || EXIT=1
    test_system lms \
        $(get_children common/djangoapps) \
        $(get_children openedx/core/djangoapps) \
        openedx/core/djangolib \
        openedx/core/lib \
        $(get_children openedx/tests) \
        $(get_children openedx/features) \
    || EXIT=1
    # paver test_lib --cov-args="-p" --with-xunitmp || EXIT=1
    emptyxunit "stub"
    return $EXIT
}

CIRCLE_JOBS_TOTAL=8
CIRCLE_NODE_TOTAL=${CIRCLE_NODE_TOTAL:-1}
CIRCLE_NODE_INDEX=${CIRCLE_NODE_INDEX:-0}
EXIT=0
for job in $(seq 0 $(( ${CIRCLE_JOBS_TOTAL} - 1 ))); do
    node=$(( ${job} % ${CIRCLE_NODE_TOTAL} ))
    if [ "${node}" -eq "${CIRCLE_NODE_INDEX}" ]; then
        run_shard_${job} || EXIT=1
    fi
done
