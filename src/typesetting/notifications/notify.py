from events import logic as events_logic


def event_typesetting_assignment(request, assignment, message, skip):
    kwargs = {
        'assignment': assignment,
        'request': request,
        'message': message,
        'skip': skip,
    }

    events_logic.Events.raise_event(
        events_logic.Events.ON_TYPESETTING_ASSIGN_NOTIFICATION,
        task_object=assignment.round.article,
        **kwargs,
    )

    if not skip:
        assignment.notified = True
        assignment.save()


def event_decision_notification(assignment, request, note, decision):
    kwargs = {
        'assignment': assignment,
        'request': request,
        'note': note,
        'decision': decision,
    }

    events_logic.Events.raise_event(
        events_logic.Events.ON_TYPESETTING_ASSIGN_DECISION,
        task_object=assignment.round.article,
        **kwargs,
    )


def event_typesetting_cancelled(assignment, request):
    kwargs = {
        'assignment': assignment,
        'request': request,
    }

    events_logic.Events.raise_event(
        events_logic.Events.ON_TYPESETTING_ASSIGN_CANCELLED,
        task_object=assignment.round.article,
        **kwargs,
    )


def event_typesetting_deleted(assignment, request):
    kwargs = {
        'assignment': assignment,
        'request': request,
    }

    events_logic.Events.raise_event(
        events_logic.Events.ON_TYPESETTING_ASSIGN_DELETED,
        task_object=assignment.round.article,
        **kwargs,
    )


def event_complete_notification(assignment, request):
    kwargs = {
        'assignment': assignment,
        'request': request,
    }

    events_logic.Events.raise_event(
        events_logic.Events.ON_TYPESETTING_ASSIGN_COMPLETE,
        task_object=assignment.round.article,
        **kwargs,
    )


def galley_proofing_assignment(request, assignment, message, skip):
    kwargs = {
        'assignment': assignment,
        'request': request,
        'message': message,
        'skip': skip,
    }

    events_logic.Events.raise_event(
        events_logic.Events.ON_PROOFREADER_ASSIGN_NOTIFICATION,
        task_object=assignment.round.article,
        **kwargs,
    )


def galley_proofing_cancel(request, assignment):
    kwargs = {
        'assignment': assignment,
        'request': request,
        'event_type': 'cancelled',
    }

    events_logic.Events.raise_event(
        events_logic.Events.ON_PROOFREADER_ASSIGN_CANCELLED,
        task_object=assignment.round.article,
        **kwargs,
    )


def galley_proofing_reset(request, assignment):
    kwargs = {
        'assignment': assignment,
        'request': request,
        'event_type': 'reset',
    }

    events_logic.Events.raise_event(
        events_logic.Events.ON_PROOFREADER_ASSIGN_RESET,
        task_object=assignment.round.article,
        **kwargs,
    )


def galley_proofing_complete(request, assignment):
    kwargs = {
        'assignment': assignment,
        'request': request,
        'event_type': 'completed'
    }

    events_logic.Events.raise_event(
        events_logic.Events.ON_PROOFREADER_ASSIGN_COMPLETE,
        task_object=assignment.round.article,
        **kwargs,
    )
