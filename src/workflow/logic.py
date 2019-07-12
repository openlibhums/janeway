def stages_in_between(from_stage, to_stage, article):
    """
    Works out the stages an article has been inbetween the two given stages.
    :param from_stage: stage name, string
    :param to_stage: stage_name, string
    :param article: Article object
    :return: list of stages in reverse order
    """
    stages = [log.element.stage for log in article.workflow_stages().reverse()]
    stage_index = stages.index(to_stage)

    return stages[:stage_index+1]


def move_to_stage(from_stage, to_stage, article):
    stages_to_process = stages_in_between(from_stage, to_stage, article)

    # TODO: Loop through the stages and call a function to reverse process
    # the stage.

    return stages_to_process