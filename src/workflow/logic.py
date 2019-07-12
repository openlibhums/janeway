def stages_in_between(from_stage, to_stage, article):
    """
    Works out the stages an article has been inbetween the two given stages.
    :param from_stage: stage name, string
    :param to_stage: stage_name, string
    :param article: Article object
    :return: list of stages in reverse order
    """
    # TODO: Get all of the stages the given article has been to inbetween
    # the two given stages and return a list in reverse order.


def move_to_stage(from_stage, to_stage, article):
    stages_to_process = stages_in_between(from_stage, to_stage, article)

    # TODO: Loop through the stages and call a function to reverse process
    # the stage.