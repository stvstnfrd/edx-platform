#!/usr/bin/env bash
set -e

###############################################################################
#
#   all-tests.sh
#
#   Execute tests for edx-platform. This script is designed to be the
#   entry point for various CI systems.
#
###############################################################################

# Violations thresholds for failing the build
<<<<<<< HEAD
export PYLINT_THRESHOLD=3850
export ESLINT_THRESHOLD=9951
=======
export PYLINT_THRESHOLD=3600
export ESLINT_THRESHOLD=10122
>>>>>>> f9fa460a74446b533b356e754848af6f56c141a1

XSSLINT_THRESHOLDS=`cat scripts/xsslint_thresholds.json`
export XSSLINT_THRESHOLDS=${XSSLINT_THRESHOLDS//[[:space:]]/}

doCheckVars() {
    if [ -n "$CIRCLECI" ] ; then
        SCRIPT_TO_RUN=scripts/circle-ci-tests.sh

    elif [ -n "$JENKINS_HOME" ] ; then
        source scripts/jenkins-common.sh
        SCRIPT_TO_RUN=scripts/generic-ci-tests.sh
    fi
}

# Determine the CI system for the environment
doCheckVars

# Run appropriate CI system script
if [ -n "$SCRIPT_TO_RUN" ] ; then
    $SCRIPT_TO_RUN

    # Exit with the exit code of the called script
    exit $?
else
    echo "ERROR. Could not detect continuous integration system."
    exit 1
fi
