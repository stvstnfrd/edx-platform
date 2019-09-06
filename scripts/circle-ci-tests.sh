#!/usr/bin/env bash
# Exit immediately if any untested command fails
set -e

# Return status is that of the last command to fail in a
# piped command, or a zero if they all succeed.
set -o pipefail

# There is no need to install the prereqs, as this was already
# just done via the dependencies override section of circle.yml.
export NO_PREREQ_INSTALL='true'

CIRCLE_JOBS_TOTAL=8
CIRCLE_NODE_TOTAL=${CIRCLE_NODE_TOTAL:-1}
CIRCLE_NODE_INDEX=${CIRCLE_NODE_INDEX:-0}
CIRCLE_TEST_REPORTS=${CIRCLE_TEST_REPORTS:-reports/junit}
CIRCLE_BUILD_NUM=${CIRCLE_BUILD_NUM:-1}
export TRAVIS_JOB_ID=${CIRCLE_BUILD_NUM}
mkdir -p "${CIRCLE_TEST_REPORTS}"

function empty_junit {
    name=${1:-empty}
    cat > ${CIRCLE_TEST_REPORTS}/${name}.xml <<END
<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="${name}" tests="1" errors="0" failures="0" skip="0">
<testcase classname="pavelib.quality" name="${name}" time="0.604"></testcase>
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
    name=${1}
    shift
    system=${1}
    shift
    random_flag=''
    if [ "${system}" == "lms" ]; then
        random_flag="--randomly-dont-reorganize"
    fi
    junit_flag="--junit-xml=${CIRCLE_TEST_REPORTS}/pytest-${system}-${name}.xml"
    cover_flags="--cov --cov-append"
    echo "DJANGO_SETTINGS_MODULE=openedx.stanford.${system}.envs.test pytest ${junit_flag} ${random_flag} ${cover_flags} ${@}"
    DJANGO_SETTINGS_MODULE=openedx.stanford.${system}.envs.test pytest ${junit_flag} ${random_flag} ${cover_flags} ${@}
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
            lms.djangoapps.class_dashboard) ;&
            lms.djangoapps.courseware) ;&
            lms.djangoapps.django_comment_client) ;&
            lms.djangoapps.instructor) ;&
            lms.djangoapps.lti_provider) ;&
            lms.djangoapps.shoppingcart) ;&
            lms.djangoapps.verify_student) ;&
            openedx.core.djangoapps.auth_exchange) ;&
            openedx.core.djangoapps.bookmarks) ;&
            openedx.core.djangoapps.catalog) ;&
            openedx.core.djangoapps.credit) ;&
            openedx.core.djangoapps.dark_lang) ;&
            openedx.core.djangoapps.external_auth) ;&
            openedx.core.djangoapps.lang_pref) ;&
            openedx.core.djangoapps.oauth_dispatch) ;&
            openedx.core.djangoapps.request_cache) ;&
            openedx.core.djangoapps.user_api) ;&
            openedx.stanford.cms.djangoapps.contentstore) ;&
            openedx.stanford.djangoapps.auth_lagunita) ;&
            openedx.stanford.djangoapps.register_cme) ;&
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
            openedx.features.course_experience)
            # SEG_FAULT
            # lms.djangoapps.mobile_api)
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
    EXIT=0
    run_paver_quality find_fixme || { EXIT=1; }
    run_paver_quality run_pep8 || { EXIT=1; }
    run_paver_quality run_pylint --system="cms,common,lms,openedx,pavelib" || { EXIT=1; }
    ## BROKE: run_paver_quality run_eslint -l ${ESLINT_THRESHOLD} || { EXIT=1; }
    run_paver_quality run_stylelint -l ${STYLELINT_THRESHOLD} || { EXIT=1; }
    run_paver_quality run_quality -p 80 || EXIT=1
    run_paver_quality run_complexity || echo "Unable to calculate code complexity. Ignoring error."
    run_paver_quality run_xsslint -t $XSSLINT_THRESHOLDS || { EXIT=1; }
    return ${EXIT}
}

function run_shard_1() {
    EXIT=0
    test_system stanford-lms lms \
        openedx/stanford/lms \
    || EXIT=1
    return ${EXIT}
}

function run_shard_5() {
    EXIT=0
    test_system edx-lms lms \
        lms/lib \
        lms/tests.py \
        $(get_children lms/djangoapps) \
    || EXIT=1
    return ${EXIT}
}

function run_shard_2() {
    EXIT=0
    test_system stanford-cms cms \
        openedx/stanford/cms/djangoapps/contentstore/tests/test_bulksettings.py \
        openedx/stanford/cms/djangoapps/contentstore/tests/test_bulkupdate.py \
        openedx/stanford/cms/djangoapps/contentstore/tests/test_utilities.py \
        $(get_children openedx/stanford/cms/djangoapps) \
    || EXIT=1
    # openedx/stanford/cms/djangoapps/contentstore/tests/test_captions.py
    return ${EXIT}
}

function run_shard_6() {
    EXIT=0
    test_system edx-cms cms \
        cms/djangoapps/contentstore/management/commands/tests \
        cms/lib \
        $(get_children cms/djangoapps) \
    || EXIT=1
    # cms/djangoapps/contentstore/api/tests
    # cms/djangoapps/contentstore/tests
    # cms/djangoapps/contentstore/views/tests
    return ${EXIT}
}

function run_shard_3() {
    EXIT=0
    test_system stanford-common cms \
        openedx/stanford/common \
        $(get_children openedx/stanford/djangoapps) \
    || EXIT=1
    test_system stanford-common lms \
        openedx/stanford/common \
        $(get_children openedx/stanford/djangoapps) \
    || EXIT=1
    return $EXIT
}

function run_shard_7() {
    EXIT=0
    test_system edx-common cms \
        $(get_children common/djangoapps) \
        $(get_children openedx/core/djangoapps) \
        openedx/core/djangolib \
        openedx/core/lib \
        openedx/tests \
    || EXIT=1
    test_system edx-common lms \
        $(get_children common/djangoapps) \
        $(get_children openedx/core/djangoapps) \
        openedx/core/djangolib \
        openedx/core/lib \
        $(get_children openedx/tests) \
        $(get_children openedx/features) \
    || EXIT=1
    test_system edx-pavelib lms \
        pavelib \
    || EXIT=1
    # paver test_lib --cov-args="-p" --with-xunitmp || EXIT=1
    return $EXIT
}

_EXIT=0
empty_junit
for job in $(seq 0 $(( ${CIRCLE_JOBS_TOTAL} - 1 ))); do
    node=$(( ${job} % ${CIRCLE_NODE_TOTAL} ))
    if [ "${node}" -eq "${CIRCLE_NODE_INDEX}" ]; then
        run_shard_${job} || _EXIT=1
    fi
done
if [ -e reports/quality_junitxml ]; then
    find reports/quality_junitxml -type f -name '*.xml' -print0 | xargs -0 --no-run-if-empty cp -t "${CIRCLE_TEST_REPORTS}"
fi
exit ${_EXIT}
