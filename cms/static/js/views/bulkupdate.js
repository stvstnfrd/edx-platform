/**
 * Bulk update problem settings-related js.
 */
define(
    ["jquery", "underscore", "gettext", "moment", "jquery.cookie"],
    function($, _, gettext, moment) {

        "use strict";

        /********** Private properties ****************************************/

        var COOKIE_NAME = 'lastupdate';

        var STAGE = {
            'SUBMITTING': 0,
            'VALIDATING': 1,
            'UPDATING' : 2,
            'SUCCESS'  : 3
        };

        var STATE = {
            'READY'      : 1,
            'IN_PROGRESS': 2,
            'SUCCESS'    : 3,
            'ERROR'      : 4
        };

        var current = { stage: 0, state: STATE.READY };
        var deferred = null;
        var update = { maxAttempts: null, showAnswer: null, statusUrl: null };
        var timeout = { id: null, delay: 1000 };
        var $dom = {
            stages: $('ol.status-progress').children(),
            successStage: $('.item-progresspoint-success'),
            wrapper: $('div.wrapper-status')
        };

        /********** Private functions *****************************************/

        /**
         * Destroys any event listener BulkUpdate might have needed
         * during the process
         *
         */
        var destroyEventListeners = function () {
            $(window).off('beforeunload.bulkupdate');
        };

        /**
         * Makes BulkUpdate feedback status list visible
         *
         */
        var displayFeedbackList = function () {
            $dom.wrapper.removeClass('is-hidden');
        };

        /**
         * Makes BulkUpdate feedback status list hidden
         *
         */
        var hideFeedbackList = function () {
            $dom.wrapper.addClass('is-hidden');
        };

        /**
         * Sets the BulkUpdate in the "error" status.
         *
         * Immediately stops any further polling from the server.
         * Displays the error message at the list element that corresponds
         * to the stage where the error occurred.
         *
         * @param {string} msg Error message to display.
         * @param {int} [stage=current.stage] Stage of update process at which error occurred.
         */
        var error = function (msg, stage) {
            current.stage = Math.abs(stage || current.stage); // Could be negative
            current.state = STATE.ERROR;

            destroyEventListeners();
            clearTimeout(timeout.id);
            updateFeedbackList(msg);

            deferred.resolve();
        };

        /**
         * Initializes the event listeners
         *
         */
        var initEventListeners = function () {
            $(window).on('beforeunload.bulkupdate', function () {
                if (current.stage <= STAGE.VALIDATING) {
                    return gettext('Your bulk update request is being processed; navigating away will abort it.');
                }
            });
        };

        var clearUpdate = function () {
            $.cookie(COOKIE_NAME, null, {path: window.location.pathname});
        };

        /**
         * Stores in a cookie the current update data
         *
         * @param {boolean} [completed=false] If the update has been completed or not
         */
        var storeUpdate = function (completed) {
            $.cookie(COOKIE_NAME, JSON.stringify({
                update: update,
                date: moment().valueOf(),
                completed: completed || false
            }), {path: window.location.pathname});
        };

        /**
         * Sets the BulkUpdate on the "success" status
         *
         */
        var success = function () {
            current.state = STATE.SUCCESS;

            destroyEventListeners();
            updateFeedbackList();

            deferred.resolve();
        };

        /**
         * Updates the BulkUpdate feedback status list
         *
         * @param {string} [currStageMsg=''] The message to show on the
         *   current stage (for now only in case of error)
         */
        var updateFeedbackList = function (currStageMsg) {
            var $checkmark, $curr, $prev, $next;
            var date, successUnix, time;

            $checkmark = $dom.successStage.find('.icon');
            currStageMsg = currStageMsg || '';

            function completeStage(stage) {
                $(stage)
                    .removeClass("is-not-started is-started")
                    .addClass("is-complete");
            }

            function errorStage(stage) {
                if (!$(stage).hasClass('has-error')) {
                    $(stage)
                        .removeClass('is-started')
                        .addClass('has-error')
                        .find('p.copy')
                        .hide()
                        .after("<p class='copy error'>" + currStageMsg + "</p>");
                }
            }

            function resetStage(stage) {
                $(stage)
                    .removeClass("is-complete is-started has-error")
                    .addClass("is-not-started")
                    .find('p.error').remove().end()
                    .find('p.copy').show();
            }

            switch (current.state) {
                case STATE.READY:
                    _.map($dom.stages, resetStage);

                    break;

                case STATE.IN_PROGRESS:
                    $prev = $dom.stages.slice(0, current.stage);
                    $curr = $dom.stages.eq(current.stage);

                    _.map($prev, completeStage);
                    $curr.removeClass("is-not-started").addClass("is-started");

                    break;

                case STATE.SUCCESS:
                    successUnix = $.cookie(COOKIE_NAME).date;
                    date = moment(successUnix).utc().format('MM/DD/YYYY');
                    time = moment(successUnix).utc().format('HH:mm');

                    _.map($dom.stages, completeStage);

                    $dom.successStage
                        .find('.item-progresspoint-success-date')
                        .html('(' + date + ' at ' + time + ' UTC)');

                    break;

                case STATE.ERROR:
                    // Make all stages up to, and including, the error stage 'complete'.
                    $prev = $dom.stages.slice(0, current.stage + 1);
                    $curr = $dom.stages.eq(current.stage);
                    $next = $dom.stages.slice(current.stage + 1);

                    _.map($prev, completeStage);
                    _.map($next, resetStage);
                    errorStage($curr);

                    break;
            }

            if (current.state === STATE.SUCCESS) {
                $checkmark.removeClass('fa-square-o').addClass('fa-check-square-o');
            } else {
                $checkmark.removeClass('fa-check-square-o').addClass('fa-square-o');
            }
        };

        /********** Public functions ******************************************/

        var BulkUpdate = {

            /**
             * Cancels the update and sets the Object to the error state
             *
             * @param {string} msg Error message to display.
             * @param {int} stage Stage of update process at which error occurred.
             */
            cancel: function (msg, stage) {
                error(msg, stage);
            },

            /**
             * Entry point for server feedback
             *
             * Checks for bulk update status every `timeout` milliseconds,
             * and updates the page accordingly.
             *
             * @param {int} [stage=0] Starting stage.
             */
            pollStatus: function (stage) {
                if (current.state !== STATE.IN_PROGRESS) {
                    updateFeedbackList();
                    return;
                }

                current.stage = stage || STAGE.SUBMITTING;

                if (current.stage === STAGE.SUCCESS) {
                    success();
                    storeUpdate(true);
                } else if (current.stage < STAGE.SUBMITTING) { // Failed
                    error(gettext("Error submitting data values"));
                } else { // In progress
                    updateFeedbackList();

                    $.getJSON(update.statusUrl, function (data) {
                        timeout.id = setTimeout(function () {
                            this.pollStatus(data.UpdateStatus);
                        }.bind(this), timeout.delay);
                    }.bind(this));
                }
            },

            /**
             * Resets the BulkUpdate internally and visually
             *
             */
            reset: function () {
                current.stage = STAGE.SUBMITTING;
                current.state = STATE.READY;

                clearTimeout(timeout.id);
                clearUpdate();
                updateFeedbackList();
                hideFeedbackList();
            },

            /**
             * Show last update status from server and start sending requests
             * to the server for status updates
             *
             * @return {jQuery promise}
             */
            resume: function () {
                deferred = $.Deferred();
                console.log("Resume update", this.storedUpdate());
                update = this.storedUpdate().update;

                $.getJSON(update.statusUrl, function (data) {
                    current.stage = data.UpdateStatus;
                    if (current.stage < STAGE.SUBMITTING) {
                        current.state = STATE.ERROR;
                    } else if (current.stage == STAGE.SUCCESS) {
                        current.state = STATE.SUCCESS;
                    } else if (current.stage == STAGE.VALIDATING || current.stage == STAGE.UPDATING) {
                        current.state = STATE.IN_PROGRESS;
                    }
                    displayFeedbackList();
                    this.pollStatus(current.stage);
                }.bind(this));

                return deferred.promise();
            },

            /**
             * Starts the updating process.
             * Makes status list visible and starts showing update progress.
             *
             * @param {int} maxAttempts The new maxAttempt setting
             * @param {string} showAnswer The new showAnswer setting
             * @param {string} statusUrl The full URL to use to query the server
             *     about the update status
             * @return {jQuery promise}
             */
            start: function (maxAttempts, showAnswer, statusUrl) {
                current.state = STATE.IN_PROGRESS;
                deferred = $.Deferred();

                update.maxAttempts = maxAttempts;
                update.showAnswer = showAnswer;
                update.statusUrl = statusUrl;

                initEventListeners();
                storeUpdate();
                displayFeedbackList();
                updateFeedbackList();

                return deferred.promise();
            },

            /**
             * Fetches the previous stored update
             *
             * @return {JSON} the data of the previous update
             */
            storedUpdate: function () {
                return JSON.parse($.cookie(COOKIE_NAME));
            }
        };

        return BulkUpdate;
    });
