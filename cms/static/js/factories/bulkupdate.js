define([
    'domReady', 'js/views/bulkupdate', 'jquery', 'gettext', 'jquery.cookie'
], function(domReady, BulkUpdate, $, gettext) {

    'use strict';

    return function (updateUrl, statusUrl, defaultMaxAttempts, defaultShowAnswer) {
        var $applyMaxAttempts = $('#max-attempts .apply-checkbox'),
            $applyShowAnswer = $('#show-answer .apply-checkbox'),
            $maxAttempts = $('#max-attempts .setting-input'),
            $showAnswer = $('#show-answer .setting-input'),
            $resetBtn = $('.view-bulkupdate .reset-button'),
            $submitBtn = $('.view-bulkupdate .submit-button'),
            DEFAULT_ERROR_MESSAGES = [
                gettext('There was an error while sending your request.') + '\n',
                gettext('There was an error while validating the setting values you submitted.') + '\n',
                gettext('There was an error while updating your problem settings in our database.') + '\n'
            ],
            unloading = false,
            previousUpdate = BulkUpdate.storedUpdate(),
            SHOW_ANSWER_OPTIONS = [
                'always',
                'answered',
                'attempted',
                'closed',
                'finished',
                'past_due',
                'correct_or_past_due',
                'never'
            ];

        var onComplete = function () {
            $resetBtn.prop('disabled', false);
        };

        var onError = function(xhr) {
            var serverMsg, errMsg, stage;

            try{
                serverMsg = $.parseJSON(xhr.responseText) || {};
                errMsg = serverMsg.ErrMsg;
                if (serverMsg.hasOwnProperty('Stage')) {
                    stage = Math.abs(serverMsg.Stage);
                    BulkUpdate.cancel(DEFAULT_ERROR_MESSAGES[stage] + errMsg, stage);
                }
            } catch (e) {
                errMsg = '';
            }

            // It could be that the user is simply refreshing the page
            // so we need to be sure this is an actual error from the server
            if (!unloading) {
                $(window).off('beforeunload.update');
            }
            console.error('Error in making POST request', errMsg);
        };

        var onReset = function () {
            BulkUpdate.reset();
            $submitBtn.prop('disabled', false);
            $resetBtn.prop('disabled', true);
            $applyMaxAttempts.prop('checked', false);
            $applyShowAnswer.prop('checked', false);
            $maxAttempts.val(defaultMaxAttempts);
            $showAnswer.val(defaultShowAnswer);
        };

        $(window).on('beforeunload', function () { unloading = true; });

        var getSettingsData = function() {
            var data = {};
            if ($applyMaxAttempts.is(':checked')) {
                data.maxAttempts = $maxAttempts.val();
            } else {
                data.maxAttempts = null;
            }
            if ($applyShowAnswer.is(':checked')) {
                data.showAnswer = $showAnswer.val();
            } else {
                data.showAnswer = null;
            }
            return data;
        };

        var loadPreviousUpdate = function() {
            if (previousUpdate) {
                var maxAttempts = previousUpdate.update.maxAttempts;
                var showAnswer = previousUpdate.update.showAnswer;

                if (maxAttempts) {
                    $maxAttempts.val(previousUpdate.update.maxAttempts);
                    $applyMaxAttempts.prop('checked', true);
                }
                if (showAnswer) {
                    $showAnswer.val(previousUpdate.update.showAnswer);
                    $applyShowAnswer.prop('checked', true);
                }

                BulkUpdate.resume().then(onComplete);
            }
        };

        var validateData = function(data) {
            var msg,
                maxAttempts = data.maxAttempts,
                showAnswer = data.showAnswer;

            if (!maxAttempts && !showAnswer) {
                return false;
            }
            if (maxAttempts) {
                if (maxAttempts < 0) {
                    msg = gettext('Not a valid value for MaxAttempts. Please enter a different value.');
                    $('.error-block').html(msg).show();
                    console.error(msg);
                    return false;
                }
            }
            if (showAnswer) {
                if (SHOW_ANSWER_OPTIONS.indexOf(showAnswer) < 0) {
                    msg = gettext('Not a valid value for ShowAnswer. Please enter a different value.');
                    $('.error-block').html(msg).show();
                    console.error(msg);
                    return false;
                }
            }
            return true;
        };

        var onSubmit = function() {
            var data = getSettingsData();
            if (validateData(data)) {
                BulkUpdate.start(
                    data.maxAttempts,
                    data.showAnswer,
                    statusUrl.replace(
                        'fillerMaxAttempts/fillerShowAnswer',
                        data.maxAttempts + '/' + data.showAnswer
                    )
                );

                BulkUpdate.pollStatus();
                $submitBtn.prop('disabled', true);

                $.ajax({
                    type: "POST",
                    data: data,
                    url: updateUrl,
                    complete: function() {
                        onComplete();
                    },
                    error: function(xhr){
                        onError(xhr);
                    },
                    success: function(){
                        console.log('Successfully made POST request');
                    },
                    dataType: 'json'
                });
            }
            return false;
        };

        domReady(function () {
            loadPreviousUpdate();

            $resetBtn.bind('click', function (e) {
                e.preventDefault();
                onReset();
            });
            $submitBtn.bind('click', function (e) {
                e.preventDefault();
                onSubmit(e);
            });

            if (previousUpdate) {
                $resetBtn.prop('disabled', false);
                $submitBtn.prop('disabled', true);
            } else {
                $resetBtn.prop('disabled', true);
                $submitBtn.prop('disabled', false);
            }
        });
    };
});
