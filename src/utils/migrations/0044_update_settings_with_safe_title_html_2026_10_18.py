from django.db import migrations
from utils import migration_utils


SETTINGS_TO_UPDATE = {
    ("email", "editor_assignment"): {
        "old_value": '<p>Dear {{ editor.salutation_name }}, </p><p>You have been assigned as an editor to "{{ article.safe_title }}" in the journal {{ request.journal.name }}.</p><p>If you are unable to be the editor for this article, please reply to this email.</p><p>You can view this article\'s data on the journal site: {{ review_in_review_url }} </p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ editor.salutation_name }}, </p><p>You have been assigned as an editor to "{{ article.safe_title_html }}" in the journal {{ request.journal.name }}.</p><p>If you are unable to be the editor for this article, please reply to this email.</p><p>You can view this article\'s data on the journal site: {{ review_in_review_url }} </p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    },
    ("email", "reviewer_acknowledgement"): {
        "old_value": 'Dear {{ review_assignment.editor.salutation_name }},<br/><br/>This is a notification that the reviewer {{ review_assignment.reviewer.full_name }} has responded to your review request for " #{{ article.pk }}: {{ article.safe_title }}" in {{ article.journal.name }} and have {{ reviewer_decision }} to perform the review. You can view more information on the journal site: {{ review_in_review_url }} ',
        "new_value": 'Dear {{ review_assignment.editor.salutation_name }},<br/><br/>This is a notification that the reviewer {{ review_assignment.reviewer.full_name }} has responded to your review request for " #{{ article.pk }}: {{ article.safe_title_html }}" in {{ article.journal.name }} and have {{ reviewer_decision }} to perform the review. You can view more information on the journal site: {{ review_in_review_url }} ',
    },
    ("email", "review_accept_acknowledgement"): {
        "old_value": 'Dear {{ review_assignment.reviewer.salutation_name }}, <br/><br/>Thank you for agreeing to review "{{ article.safe_title }}" in {{ article.journal.name }}. <br/><br/>You can now access the manuscript and the review process at: {{ review_url }}  <br/><br/>Regards, <br/>{{ review_assignment.editor.signature|safe }}',
        "new_value": 'Dear {{ review_assignment.reviewer.salutation_name }}, <br/><br/>Thank you for agreeing to review "{{ article.safe_title_html }}" in {{ article.journal.name }}. <br/><br/>You can now access the manuscript and the review process at: {{ review_url }}  <br/><br/>Regards, <br/>{{ review_assignment.editor.signature|safe }}',
    },
    ("email", "review_complete_reviewer_acknowledgement"): {
        "old_value": '<p>Dear {{ review_assignment.reviewer.salutation_name }}, </p><p>Thank you for completing your review of "{{ article.safe_title }}" in {{ article.journal.name }}. </p><p>We are extremely grateful for the work of reviewers, which greatly enhances the quality of the journal. </p><p>Thank you again and regards,</p><p>{{ review_assignment.editor.signature|safe }}</p>',
        "new_value": '<p>Dear {{ review_assignment.reviewer.salutation_name }}, </p><p>Thank you for completing your review of "{{ article.safe_title_html }}" in {{ article.journal.name }}. </p><p>We are extremely grateful for the work of reviewers, which greatly enhances the quality of the journal. </p><p>Thank you again and regards,</p><p>{{ review_assignment.editor.signature|safe }}</p>',
    },
    ("email", "review_request_sent"): {
        "old_value": 'Dear {{ review_assignment.editor.salutation_name }}, <br><br>This is a notification that the reviewer status on "{{ article.safe_title }}" in {{ article.journal.name }} has been <a href="{% journal_url \'review_in_review\' review_assignment.article.pk  %}">updated</a>. <br><br>Regards, <br>{{ request.user.signature|safe }}',
        "new_value": 'Dear {{ review_assignment.editor.salutation_name }}, <br><br>This is a notification that the reviewer status on "{{ article.safe_title_html }}" in {{ article.journal.name }} has been <a href="{% journal_url \'review_in_review\' review_assignment.article.pk  %}">updated</a>. <br><br>Regards, <br>{{ request.user.signature|safe }}',
    },
    ("email", "review_decline_acknowledgement"): {
        "old_value": 'Dear {{ review_assignment.reviewer.salutation_name }}, \n\nThank you for letting us know that you are unable to review "{{ article.safe_title }}" in {{ article.journal.name }}.\n\n We are most grateful for your time.\n\nRegards,\n{{ request.user.signature|safe }}',
        "new_value": 'Dear {{ review_assignment.reviewer.salutation_name }}, \n\nThank you for letting us know that you are unable to review "{{ article.safe_title_html }}" in {{ article.journal.name }}.\n\n We are most grateful for your time.\n\nRegards,\n{{ request.user.signature|safe }}',
    },
    ("email", "review_assignment"): {
        "old_value": 'Dear {{ review_assignment.reviewer.salutation_name }},<br/><br/>We are requesting that you undertake a review of "{{ article.safe_title }}" in {{ article.journal.name }}.<br/><br/>We would be most grateful for your time as the feedback from our reviewers is of the utmost importance to our editorial decision-making processes.<br/><br/>You can let us know your decision or decline to undertake the review: {{ review_url }} <br/><br/>{{ article_details }}<br/><br/>Regards,<br/>{{ request.user.signature|safe }}',
        "new_value": 'Dear {{ review_assignment.reviewer.salutation_name }},<br/><br/>We are requesting that you undertake a review of "{{ article.safe_title_html }}" in {{ article.journal.name }}.<br/><br/>We would be most grateful for your time as the feedback from our reviewers is of the utmost importance to our editorial decision-making processes.<br/><br/>You can let us know your decision or decline to undertake the review: {{ review_url }} <br/><br/>{{ article_details }}<br/><br/>Regards,<br/>{{ request.user.signature|safe }}',
    },
    ("email", "default_review_reminder"): {
        "old_value": 'Dear {{ review_assignment.reviewer.salutation_name }},<br/><br/>We recently sent you an email requesting that you undertake a review of "{{ article.safe_title }}" in {{ article.journal.name }}.<br/><br/>We would be most grateful for your time as the feedback from our reviewers is of the utmost importance to our editorial decision-making processes.<br/><br/>We would appreciate it if you could let us know your decision or decline to undertake the review: {{ review_url }} <br/><br/>Regards,<br/>{{ request.user.signature|safe }}',
        "new_value": 'Dear {{ review_assignment.reviewer.salutation_name }},<br/><br/>We recently sent you an email requesting that you undertake a review of "{{ article.safe_title_html }}" in {{ article.journal.name }}.<br/><br/>We would be most grateful for your time as the feedback from our reviewers is of the utmost importance to our editorial decision-making processes.<br/><br/>We would appreciate it if you could let us know your decision or decline to undertake the review: {{ review_url }} <br/><br/>Regards,<br/>{{ request.user.signature|safe }}',
    },
    ("email", "accepted_review_reminder"): {
        "old_value": 'Dear {{ review_assignment.reviewer.salutation_name }},<br/><br/>You recently agreed undertake a review of "{{ article.safe_title }}" in {{ article.journal.name }}.<br/><br/>We would be most grateful for your time as the feedback from our reviewers is of the utmost importance to our editorial decision-making processes.<br/><br/>Check our site to undertake the review: {{ review_url }} <br/><br/>Regards,<br/>{{ request.user.signature|safe }}',
        "new_value": 'Dear {{ review_assignment.reviewer.salutation_name }},<br/><br/>You recently agreed undertake a review of "{{ article.safe_title_html }}" in {{ article.journal.name }}.<br/><br/>We would be most grateful for your time as the feedback from our reviewers is of the utmost importance to our editorial decision-making processes.<br/><br/>Check our site to undertake the review: {{ review_url }} <br/><br/>Regards,<br/>{{ request.user.signature|safe }}',
    },
    ("email", "review_decision_accept"): {
        "old_value": '<p>Dear {{ article.correspondence_author.salutation_name|se_can_see_pii:article }},<br/><br/>We are happy to inform you that your article, "{{ article.safe_title }}", has been accepted in {{ article.journal.name }}. Thank you for submitting such a strong manuscript.<br/></p><p>Peer review reports and feedback on the manuscript can be viewed at: {{ review_url }} </p><p>We will be back in touch soon to discuss the next stages of production.</p><p><br/>Regards,</p><p><br/>{{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ article.correspondence_author.salutation_name|se_can_see_pii:article }},<br/><br/>We are happy to inform you that your article, "{{ article.safe_title_html }}", has been accepted in {{ article.journal.name }}. Thank you for submitting such a strong manuscript.<br/></p><p>Peer review reports and feedback on the manuscript can be viewed at: {{ review_url }} </p><p>We will be back in touch soon to discuss the next stages of production.</p><p><br/>Regards,</p><p><br/>{{ request.user.signature|safe }}</p>',
    },
    ("email", "review_decision_decline"): {
        "old_value": '<p>Dear {{ article.correspondence_author.salutation_name|se_can_see_pii:article }},<br><br>We are sorry to inform you that "{{ article.safe_title }}" has been declined in {{ article.journal.name }}.<br><br>You can view your reviews and feedback on the manuscript at: {{ review_url }} <br><br>Regards,</p><p>{{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ article.correspondence_author.salutation_name|se_can_see_pii:article }},<br><br>We are sorry to inform you that "{{ article.safe_title_html }}" has been declined in {{ article.journal.name }}.<br><br>You can view your reviews and feedback on the manuscript at: {{ review_url }} <br><br>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    },
    ("email", "review_decision_undecline"): {
        "old_value": '<p>Dear {{ article.correspondence_author.salutation_name }},<br><br>We wish to inform you that the earlier decision to decline "{{ article.safe_title }}" in {{ article.journal.name }} has been reversed. The article is now being reconsidered.<br><br>Regards,</p><p>{{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ article.correspondence_author.salutation_name }},<br><br>We wish to inform you that the earlier decision to decline "{{ article.safe_title_html }}" in {{ article.journal.name }} has been reversed. The article is now being reconsidered.<br><br>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    },
    ("email", "unassign_editor"): {
        "old_value": '<p>Dear {{ assignment.editor.salutation_name }},</p><p>We are writing to let you know that you have been unassigned from the article "{{ article.safe_title }}" in {{ article.journal.name }}.</p><p>Regards,</p>{{ request.user.signature|safe }}',
        "new_value": '<p>Dear {{ assignment.editor.salutation_name }},</p><p>We are writing to let you know that you have been unassigned from the article "{{ article.safe_title_html }}" in {{ article.journal.name }}.</p><p>Regards,</p>{{ request.user.signature|safe }}',
    },
    ("email", "review_withdrawl"): {
        "old_value": '<p>Dear {{ review_assignment.reviewer.salutation_name }},</p><p>We are writing to let you know that the review request for "{{ article.safe_title }}" in {{ article.journal.name }} has been cancelled.</p><p>We thank you for your time but your review is no longer required.</p><p>Regards,</p>{{ request.user.signature|safe }}',
        "new_value": '<p>Dear {{ review_assignment.reviewer.salutation_name }},</p><p>We are writing to let you know that the review request for "{{ article.safe_title_html }}" in {{ article.journal.name }} has been cancelled.</p><p>We thank you for your time but your review is no longer required.</p><p>Regards,</p>{{ request.user.signature|safe }}',
    },
    ("email", "copyeditor_assignment_notification"): {
        "old_value": '<p>Dear {{ assignment.copyeditor.salutation_name }},<br/><br/>We are requesting that your undertake a copyedit for the article "{{ assignment.article.safe_title }}".<br/><br/>This assignment is due on {{ assignment.due }}. You can access this task on the\xa0journal site: {{ copyedit_requests_url }} </p><p><br/>Regards,</p><p>{{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ assignment.copyeditor.salutation_name }},<br/><br/>We are requesting that your undertake a copyedit for the article "{{ assignment.article.safe_title_html }}".<br/><br/>This assignment is due on {{ assignment.due }}. You can access this task on the\xa0journal site: {{ copyedit_requests_url }} </p><p><br/>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    },
    ("email", "copyeditor_reopen_task"): {
        "old_value": 'Dear {{ assignment.copyeditor.salutation_name }},<br/><br/>We are requesting further copyedits article "{{ assignment.article.safe_title }}". You can access this task on the\xa0journal site: {{ copyedit_requests_url }} <br/><br/>[ADD FEEDBACK HERE].<br/><br/>Regards, <br/>{{ request.user.signature|safe }}',
        "new_value": 'Dear {{ assignment.copyeditor.salutation_name }},<br/><br/>We are requesting further copyedits article "{{ assignment.article.safe_title_html }}". You can access this task on the\xa0journal site: {{ copyedit_requests_url }} <br/><br/>[ADD FEEDBACK HERE].<br/><br/>Regards, <br/>{{ request.user.signature|safe }}',
    },
    ("email", "production_manager_notification"): {
        "old_value": "<p>Dear {{ production_assignment.production_manager.salutation_name }},</p><p>This is an automatic notification from {{ request.user.full_name }} that you have been assigned to the production of article {{ production_assignment.article.safe_title }}. You can view further information on this here: {{ production_article_url }} </p><p>Regards,</p>",
        "new_value": "<p>Dear {{ production_assignment.production_manager.salutation_name }},</p><p>This is an automatic notification from {{ request.user.full_name }} that you have been assigned to the production of article {{ production_assignment.article.safe_title_html }}. You can view further information on this here: {{ production_article_url }} </p><p>Regards,</p>",
    },
    ("email", "typesetter_notification"): {
        "old_value": "<p>Dear {{ typeset_task.typesetter.salutation_name }},</p><p>This is a notification from {{ request.user.full_name }} that you have been assigned to the production of article {{ typeset_task.assignment.article.safe_title }}. </p><p>You can view further information on this here: {{ typesetter_requests_url }} </p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>",
        "new_value": "<p>Dear {{ typeset_task.typesetter.salutation_name }},</p><p>This is a notification from {{ request.user.full_name }} that you have been assigned to the production of article {{ typeset_task.assignment.article.safe_title_html }}. </p><p>You can view further information on this here: {{ typesetter_requests_url }} </p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>",
    },
    ("email", "typesetter_complete_notification"): {
        "old_value": "<p>Dear {{ production_assignment.production_manager.salutation_name }},</p><p>This is a notification from {{ request.user.full_name }} that typesetting for article {{ production_assignment.article.safe_title }} has been completed. You can view further information on the journal site.: {{ production_article_url }} /p><p>Regards,<br/></p>",
        "new_value": "<p>Dear {{ production_assignment.production_manager.salutation_name }},</p><p>This is a notification from {{ request.user.full_name }} that typesetting for article {{ production_assignment.article.safe_title_html }} has been completed. You can view further information on the journal site.: {{ production_article_url }} /p><p>Regards,<br/></p>",
    },
    ("email", "typeset_ack"): {
        "old_value": "<p>Dear {{ production_assignment.editor.salutation_name }},</p><p>Production for article {{ article.safe_title }} has been completed.</p><p>Regards</p><p>{{ request.user.signature|safe }}</p>",
        "new_value": "<p>Dear {{ production_assignment.editor.salutation_name }},</p><p>Production for article {{ article.safe_title_html }} has been completed.</p><p>Regards</p><p>{{ request.user.signature|safe }}</p>",
    },
    ("email", "production_complete"): {
        "old_value": '<p>This is a notification to inform you that Production is complete for article "{{ article.safe_title}}".</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
        "new_value": '<p>This is a notification to inform you that Production is complete for article "{{ article.safe_title_html}}".</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    },
    ("email", "notify_proofing_manager"): {
        "old_value": "<p>Dear {{ proofing_assignment.proofing_manager.salutation_name }},</p><p>You have been assigned as the Proofing Manager: {{ proofing_article_url }} for {{ article.safe_title }}.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br/></p>",
        "new_value": "<p>Dear {{ proofing_assignment.proofing_manager.salutation_name }},</p><p>You have been assigned as the Proofing Manager: {{ proofing_article_url }} for {{ article.safe_title_html }}.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br/></p>",
    },
    ("email", "notify_proofreader_complete"): {
        "old_value": '<p>Dear {{ proofing_task.round.assignment.proofing_manager.salutation_name }},<br/><br/>I have completed proofreading: {{ proofing_article_url }} for "{{ proofing_task.round.assignment.article.safe_title }}".<br/></p><p><br/>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br/></p>',
        "new_value": '<p>Dear {{ proofing_task.round.assignment.proofing_manager.salutation_name }},<br/><br/>I have completed proofreading: {{ proofing_article_url }} for "{{ proofing_task.round.assignment.article.safe_title_html }}".<br/></p><p><br/>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br/></p>',
    },
    ("email", "notify_proofreader_assignment"): {
        "old_value": '<p>Dear {{ proofing_task.proofreader.salutation_name }},</p><p>You have been assigned a proofreading task: {{ proofing_requests_url }} for "{{ article.safe_title }}". We would be most grateful for your assistance in proofreading this article.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br/></p>',
        "new_value": '<p>Dear {{ proofing_task.proofreader.salutation_name }},</p><p>You have been assigned a proofreading task: {{ proofing_requests_url }} for "{{ article.safe_title_html }}". We would be most grateful for your assistance in proofreading this article.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br/></p>',
    },
    ("email", "notify_typesetter_proofing_changes"): {
        "old_value": '<p>Dear {{ typesetter_proofing_task.typesetter.salutation_name }},</p><p>Changes have been requested for article "{{ article.safe_title }}".</p><p>You can access this request from the requests page: {{ proofing_requests_url }} /p><p>Regards,<br/></p><p>{{ request.user.signature|safe }}</p><p><br/></p>',
        "new_value": '<p>Dear {{ typesetter_proofing_task.typesetter.salutation_name }},</p><p>Changes have been requested for article "{{ article.safe_title_html }}".</p><p>You can access this request from the requests page: {{ proofing_requests_url }} /p><p>Regards,<br/></p><p>{{ request.user.signature|safe }}</p><p><br/></p>',
    },
    ("email", "thank_proofreaders_and_typesetters"): {
        "old_value": '<p>Dear {{ user.salutation_name }}</p><p>Thank you for your efforts during the production of "{{ article.safe_title }}".</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br></p>',
        "new_value": '<p>Dear {{ user.salutation_name }}</p><p>Thank you for your efforts during the production of "{{ article.safe_title_html }}".</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br></p>',
    },
    ("email", "notify_editor_proofing_complete"): {
        "old_value": '<p>Dear {{ proofing_assignment.editor.salutation_name }},</p><p>Proofing for "{{ article.safe_title }}" is now complete.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br/></p>',
        "new_value": '<p>Dear {{ proofing_assignment.editor.salutation_name }},</p><p>Proofing for "{{ article.safe_title_html }}" is now complete.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p><p><br/></p>',
    },
    ("email", "notify_proofreader_cancelled"): {
        "old_value": '<p>Dear {{ proofing_task.proofreader.salutation_name }},<br><br>The proofreading task for "{{ proofing_task.round.assignment.article.safe_title }}" that was due on {{ proofing_task.due }} has been cancelled.</p><p><br>{% if user_content_message %}{{ user_content_message|safe }}{% endif %}</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ proofing_task.proofreader.salutation_name }},<br><br>The proofreading task for "{{ proofing_task.round.assignment.article.safe_title_html }}" that was due on {{ proofing_task.due }} has been cancelled.</p><p><br>{% if user_content_message %}{{ user_content_message|safe }}{% endif %}</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    },
    ("email", "author_publication"): {
        "old_value": "<p>Dear {{ article.correspondence_author.salutation_name }}<br><br>We are pleased to say that your article, \"{{ article.safe_title }}\", is set for publication on {{ article.date_published|date:'Y-m-d' }} at {{ article.date_published|date:'H:i' }} {{ article.date_published.tzinfo.zone }}.</p><p>You may want to consider one or more of the following in order to promote your research:</p><ul><li>Email a link to your paper to colleagues</li><li>Write a blog post about your paper</li><li>Upload it to your institutional repository or a subject repository.</li><li>Add to Wikipedia <a href=\"https://en.wikipedia.org/wiki/Wikipedia:Research_help/Scholars_and_experts\">where appropriate</a></li></ul><p>Regards,<br></p><p>{{ request.user.signature|safe }}</p>",
        "new_value": "<p>Dear {{ article.correspondence_author.salutation_name }}<br><br>We are pleased to say that your article, \"{{ article.safe_title_html }}\", is set for publication on {{ article.date_published|date:'Y-m-d' }} at {{ article.date_published|date:'H:i' }} {{ article.date_published.tzinfo.zone }}.</p><p>You may want to consider one or more of the following in order to promote your research:</p><ul><li>Email a link to your paper to colleagues</li><li>Write a blog post about your paper</li><li>Upload it to your institutional repository or a subject repository.</li><li>Add to Wikipedia <a href=\"https://en.wikipedia.org/wiki/Wikipedia:Research_help/Scholars_and_experts\">where appropriate</a></li></ul><p>Regards,<br></p><p>{{ request.user.signature|safe }}</p>",
    },
    ("email", "draft_message"): {
        "old_value": "A section editor has made a draft decision: {{ review_in_review_url }} regarding an article in your section: {{ article.safe_title }}.<br/><br/>The draft decision is [[DECISION TEXT ]].<br/><br/>Regards,<br/><br/>{{ request.user.signature|safe }} ",
        "new_value": "A section editor has made a draft decision: {{ review_in_review_url }} regarding an article in your section: {{ article.safe_title_html }}.<br/><br/>The draft decision is [[DECISION TEXT ]].<br/><br/>Regards,<br/><br/>{{ request.user.signature|safe }} ",
    },
    ("email", "draft_editor_message"): {
        "old_value": "<p>{{ draft.section_editor.full_name }} has drafted a decision for {{ article.safe_title }}.</p><p>The section editor provided the following message:</p><p>{{ draft.message_to_editor|safe }}</p><p>You can view the draft decision on the\xa0journal site: {{ review_edit_draft_decision_url }} <br/></p>",
        "new_value": "<p>{{ draft.section_editor.full_name }} has drafted a decision for {{ article.safe_title_html }}.</p><p>The section editor provided the following message:</p><p>{{ draft.message_to_editor|safe }}</p><p>You can view the draft decision on the\xa0journal site: {{ review_edit_draft_decision_url }} <br/></p>",
    },
    ("email", "editor_new_submission"): {
        "old_value": "A new article, {{ article.safe_title }}, has been submitted.<br/><br/>You can assign an editor Here: {{ review_unassigned_article_url }} <br/><br/>Regards, <br/>",
        "new_value": "A new article, {{ article.safe_title_html }}, has been submitted.<br/><br/>You can assign an editor Here: {{ review_unassigned_article_url }} <br/><br/>Regards, <br/>",
    },
    ("email", "section_editor_pub_notification"): {
        "old_value": "<p>Dear {{ editor.salutation_name }},</p><p>An article that you served as section editor for, {{ article.safe_title }}, has been set for publication.<br><br>The article will be published on {{ article.date_published }}<br><br>Regards,",
        "new_value": "<p>Dear {{ editor.salutation_name }},</p><p>An article that you served as section editor for, {{ article.safe_title_html }}, has been set for publication.<br><br>The article will be published on {{ article.date_published }}<br><br>Regards,",
    },
    ("email", "peer_reviewer_pub_notification"): {
        "old_value": '<p>Dear reviewers,</p><p>An article that you served as peer reviewer for, "{{ article.safe_title }}", has been set for publication.<br><br>The article will be published on {{ article.date_published }}.<br><br>Regards,',
        "new_value": '<p>Dear reviewers,</p><p>An article that you served as peer reviewer for, "{{ article.safe_title_html }}", has been set for publication.<br><br>The article will be published on {{ article.date_published }}.<br><br>Regards,',
    },
    ("email", "editor_digest"): {
        "old_value": "<p>Unassigned Articles:</p><ul>{% for article in unassigned_articles %}<li>{{ article.safe_title }}</li>{% endfor %}</ul><p>Overdue Reviews</p><ul>{% for review in overdue_reviews %}<li>{{ review.reviewer.full_name }} for article {{ review.article.safe_title }}.</li>{% endfor %}</ul><p>Overdue Revisions</p><ul>{% for revision in overdue_revisions %}<li>{{ revision.article.correspondence_author.full_name }} for article {{ review.article.safe_title }}.</li>{% endfor %}</ul><p>Overdue Proofing</p><ul>{% for proofing in overdue_proofing %}<li>{{ proofing.proofreader.full_name }} for article {{ proofing.round.assignment.article.safe_title }}</li>{% endfor %}</ul><p>Awaiting Publication</p><ul>{% for article in awaiting_publication %}<li>{{ article.safe_title }}</li>{% endfor %}</ul>",
        "new_value": "<p>Unassigned Articles:</p><ul>{% for article in unassigned_articles %}<li>{{ article.safe_title_html }}</li>{% endfor %}</ul><p>Overdue Reviews</p><ul>{% for review in overdue_reviews %}<li>{{ review.reviewer.full_name }} for article {{ review.article.safe_title_html }}.</li>{% endfor %}</ul><p>Overdue Revisions</p><ul>{% for revision in overdue_revisions %}<li>{{ revision.article.correspondence_author.full_name }} for article {{ review.article.safe_title_html }}.</li>{% endfor %}</ul><p>Overdue Proofing</p><ul>{% for proofing in overdue_proofing %}<li>{{ proofing.proofreader.full_name }} for article {{ proofing.round.assignment.article.safe_title_html }}</li>{% endfor %}</ul><p>Awaiting Publication</p><ul>{% for article in awaiting_publication %}<li>{{ article.safe_title_html }}</li>{% endfor %}</ul>",
    },
    ("email", "reviewer_digest"): {
        "old_value": "<p>Review Requests</p><ul>{% for review in pending_requests %}<li>{{ review.article.safe_title }} due on {{ review.date_due }}</li>{% endfor %}</ul><p>Overdue Requests</p><ul>{% for review in overdue_requests %}<li>{{ review.article.safe_title }} due on {{ review.date_due }}</li>{% endfor %}</ul>",
        "new_value": "<p>Review Requests</p><ul>{% for review in pending_requests %}<li>{{ review.article.safe_title_html }} due on {{ review.date_due }}</li>{% endfor %}</ul><p>Overdue Requests</p><ul>{% for review in overdue_requests %}<li>{{ review.article.safe_title_html }} due on {{ review.date_due }}</li>{% endfor %}</ul>",
    },
    ("email", "revision_digest"): {
        "old_value": "<p>Revision Requests</p><ul>{% for revision in pending_requests %}<li>{{ revision.article.safe_title }} due on {{ revision.date_due }}</li>{% endfor %}</ul><p>Overdue Requests</p><ul>{% for revision in overdue_requests %}<li>{{ revision.article.safe_title }} due on {{ revision.date_due }}</li>{% endfor %}</ul>",
        "new_value": "<p>Revision Requests</p><ul>{% for revision in pending_requests %}<li>{{ revision.article.safe_title_html }} due on {{ revision.date_due }}</li>{% endfor %}</ul><p>Overdue Requests</p><ul>{% for revision in overdue_requests %}<li>{{ revision.article.safe_title_html }} due on {{ revision.date_due }}</li>{% endfor %}</ul>",
    },
    ("email", "production_assign_article"): {
        "old_value": "<p>Dear {{ user.salutation_name }}<br/><br/>This is an automatic notification from {{ request.journal.name }} that you have been assigned to the production of article {{ article.safe_title }}. You can view further information on this on the journal site: {{ url }} </p><p>Regards,</p>",
        "new_value": "<p>Dear {{ user.salutation_name }}<br/><br/>This is an automatic notification from {{ request.journal.name }} that you have been assigned to the production of article {{ article.safe_title_html }}. You can view further information on this on the journal site: {{ url }} </p><p>Regards,</p>",
    },
    ("email", "notification_submission"): {
        "old_value": '<p>Dear {{ notification.user.salutation_name }},<br/><br/>This email is to notify you that {{ article.correspondence_author.full_name }} has submitted article "{{ article.safe_title }}" to  {{ article.journal.name }}.</p><p>You can review the metadata in the journal site: {{ review_unassigned_url }} </p><p>Regards,</p>',
        "new_value": '<p>Dear {{ notification.user.salutation_name }},<br/><br/>This email is to notify you that {{ article.correspondence_author.full_name }} has submitted article "{{ article.safe_title_html }}" to  {{ article.journal.name }}.</p><p>You can review the metadata in the journal site: {{ review_unassigned_url }} </p><p>Regards,</p>',
    },
    ("email", "copyedit_updated"): {
        "old_value": '<p>Dear {{ copyedit_assignment.copyeditor.salutation_name }},</p><p>Your copyediting assignment for article "{{ copyedit_assignment.article.safe_title }}" has been updated. The due date is set to: {{ copyedit_assignment.due }}.</p><p>Regards, {{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ copyedit_assignment.copyeditor.salutation_name }},</p><p>Your copyediting assignment for article "{{ copyedit_assignment.article.safe_title_html }}" has been updated. The due date is set to: {{ copyedit_assignment.due }}.</p><p>Regards, {{ request.user.signature|safe }}</p>',
    },
    ("email", "copyedit_deleted"): {
        "old_value": '<p>Dear {{ copyedit_assignment.copyeditor.salutation_name }},</p><p>Your copyediting assignment for article "{{ copyedit_assignment.article.safe_title }}" has been deleted. We no longer require you to undertake this task.</p><p>Regards, {{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ copyedit_assignment.copyeditor.salutation_name }},</p><p>Your copyediting assignment for article "{{ copyedit_assignment.article.safe_title_html }}" has been deleted. We no longer require you to undertake this task.</p><p>Regards, {{ request.user.signature|safe }}</p>',
    },
    ("email", "typeset_deleted"): {
        "old_value": '<p>Dear {{ typeset_task.typesetter.salutation_name }},</p><p>Your typesetting assignment for article "{{ typeset_task.assignment.article.safe_title }}" has been deleted. We no longer require you to undertake this task.</p><p>Regards, {{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ typeset_task.typesetter.salutation_name }},</p><p>Your typesetting assignment for article "{{ typeset_task.assignment.article.safe_title_html }}" has been deleted. We no longer require you to undertake this task.</p><p>Regards, {{ request.user.signature|safe }}</p>',
    },
    ("email", "notify_proofreader_edited"): {
        "old_value": '<p>Dear {{ proofing_task.proofreader.salutation_name }},</p><p>Your proofing assignment for article "{{ proofing_task.assignment.article.safe_title }}" has been updated. Its due it is now {{ proofing_task.due }}. If you cannot completed the task in this time, please get in touch by replying to this email.</p><p>Regards, {{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear {{ proofing_task.proofreader.salutation_name }},</p><p>Your proofing assignment for article "{{ proofing_task.assignment.article.safe_title_html }}" has been updated. Its due it is now {{ proofing_task.due }}. If you cannot completed the task in this time, please get in touch by replying to this email.</p><p>Regards, {{ request.user.signature|safe }}</p>',
    },
    ("email", "notify_correction_cancelled"): {
        "old_value": "<p>Dear {{ correction.typesetter.salutation_name }},</p><p>The correction task you were assigned for {{ article.safe_title }} has been cancelled.</p><p>Regards,</p> {{ request.user.signature|safe }}",
        "new_value": "<p>Dear {{ correction.typesetter.salutation_name }},</p><p>The correction task you were assigned for {{ article.safe_title_html }} has been cancelled.</p><p>Regards,</p> {{ request.user.signature|safe }}",
    },
    ("email", "revisions_complete_receipt"): {
        "old_value": '<p>Dear {{ revision.article.correspondence_author.salutation_name }},</p><p>Thank you for submitting your revisions for "{{ revision.article.safe_title }}". We will be in touch with further information about your submission soon.</p><p>Best wishes,</p><p>{{ revision.editor.full_name }}</p>',
        "new_value": '<p>Dear {{ revision.article.correspondence_author.salutation_name }},</p><p>Thank you for submitting your revisions for "{{ revision.article.safe_title_html }}". We will be in touch with further information about your submission soon.</p><p>Best wishes,</p><p>{{ revision.editor.full_name }}</p>',
    },
    ("email", "author_copyedit_deleted"): {
        "old_value": '<p>Dear {{ author_review.assignment.article.correspondence_author.salutation_name }},</p><p>The copyediting review request for "{{ author_review.assignment.article.safe_title }}" that we sent you has been deleted.</p><p>Regards,</p>{{ request.user.signature|safe }}',
        "new_value": '<p>Dear {{ author_review.assignment.article.correspondence_author.salutation_name }},</p><p>The copyediting review request for "{{ author_review.assignment.article.safe_title_html }}" that we sent you has been deleted.</p><p>Regards,</p>{{ request.user.signature|safe }}',
    },
    ("email", "reader_publication_notification"): {
        "old_value": '<p>You are receiving this email because you are registered for publication notifications for {{ journal.name }}.</p><p>The following articles have been published today: </p><ul>{% for article in articles %}<li><a href="{{ article.url }}">{{ article.safe_title }}</a></li>{% endfor %}</ul>',
        "new_value": '<p>You are receiving this email because you are registered for publication notifications for {{ journal.name }}.</p><p>The following articles have been published today: </p><ul>{% for article in articles %}<li><a href="{{ article.url }}">{{ article.safe_title_html }}</a></li>{% endfor %}</ul>',
    },
    ("email", "bounced_email_notification"): {
        "old_value": '<p>An email sent to {% for email in event.to %}{{ email }}{% if not forloop.last %}, {% endif %}{% endfor %} has not been delivered.{% if target %} This message was in regards to {{ event.content_type.model }} #{{ target.pk }} "{{ target.safe_title }}".{% endif %}</p><p>Kind Regards,</p>',
        "new_value": '<p>An email sent to {% for email in event.to %}{{ email }}{% if not forloop.last %}, {% endif %}{% endfor %} has not been delivered.{% if target %} This message was in regards to {{ event.content_type.model }} #{{ target.pk }} "{{ target.safe_title_html }}".{% endif %}</p><p>Kind Regards,</p>',
    },
    ("email", "typesetting_notify_typesetter"): {
        "old_value": "<p>Dear {{ assignment.typesetter.salutation_name }},</p><p>This is a notification from {{ request.user.full_name }} that you have been assigned to the production of article {{ assignment.round.article.safe_title }} on journal {{ request.journal.name }}. </p><p>You can view further information on this assignment: {{ typesetting_assignments_url }}.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>",
        "new_value": "<p>Dear {{ assignment.typesetter.salutation_name }},</p><p>This is a notification from {{ request.user.full_name }} that you have been assigned to the production of article {{ assignment.round.article.safe_title_html }} on journal {{ request.journal.name }}. </p><p>You can view further information on this assignment: {{ typesetting_assignments_url }}.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>",
    },
    ("email", "typsetting_typesetter_decision_accept"): {
        "old_value": "<p>Dear {{ assignment.manager.salutation_name }},</p><p>This is to notify you that {{ assignment.typesetter.full_name }} has accepted your assignment your assignment for {{ assignment.round.article.safe_title }}.</p>{% if note %}<p>They provided the following note: <br />{{ note|safe }} </p>{% endif %}<p>Regards,</p>",
        "new_value": "<p>Dear {{ assignment.manager.salutation_name }},</p><p>This is to notify you that {{ assignment.typesetter.full_name }} has accepted your assignment your assignment for {{ assignment.round.article.safe_title_html }}.</p>{% if note %}<p>They provided the following note: <br />{{ note|safe }} </p>{% endif %}<p>Regards,</p>",
    },
    ("email", "typsetting_typesetter_decision_decline"): {
        "old_value": "<p>Dear {{ assignment.manager.salutation_name }},</p><p>This is to notify you that {{ assignment.typesetter.full_name }} has declined your assignment for {{ assignment.round.article.safe_title }}.</p>{% if note %}<p>They provided the following note: <br />{{ note|safe }} </p>{% endif %}<p>Regards,</p>",
        "new_value": "<p>Dear {{ assignment.manager.salutation_name }},</p><p>This is to notify you that {{ assignment.typesetter.full_name }} has declined your assignment for {{ assignment.round.article.safe_title_html }}.</p>{% if note %}<p>They provided the following note: <br />{{ note|safe }} </p>{% endif %}<p>Regards,</p>",
    },
    ("email", "typesetting_typesetter_complete"): {
        "old_value": "<p>Dear {{ assignment.manager.salutation_name }},</p><p>This is to notify you that {{ assignment.typesetter.full_name }} has completed your assignment for {{ assignment.round.article.safe_title }}.</p>{% if note %}<p>They provided the following note: <br />{{ assignment.typesetter_note|safe }} </p>{% endif %}<p>Visit the article URL for more details: {{ typesetting_article_url }}</p><p>Regards,</p>",
        "new_value": "<p>Dear {{ assignment.manager.salutation_name }},</p><p>This is to notify you that {{ assignment.typesetter.full_name }} has completed your assignment for {{ assignment.round.article.safe_title_html }}.</p>{% if note %}<p>They provided the following note: <br />{{ assignment.typesetter_note|safe }} </p>{% endif %}<p>Visit the article URL for more details: {{ typesetting_article_url }}</p><p>Regards,</p>",
    },
    ("email", "typesetting_notify_proofreader"): {
        "old_value": "<p>Dear {{ assignment.proofreader.salutation_name }},</p><p>This is an notification from {{ request.user.full_name }} that you have been assigned to proofread {{ assignment.round.article.safe_title }} on journal {{ request.journal.name }}. </p><p>You can view further information on this assignment: {{ typesetting_assignments_url }}.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>",
        "new_value": "<p>Dear {{ assignment.proofreader.salutation_name }},</p><p>This is an notification from {{ request.user.full_name }} that you have been assigned to proofread {{ assignment.round.article.safe_title_html }} on journal {{ request.journal.name }}. </p><p>You can view further information on this assignment: {{ typesetting_assignments_url }}.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>",
    },
    ("email", "typesetting_complete"): {
        "old_value": '<p>Dear editors,</p><p>This is an automatic notification to inform you that Typesetting is complete for article "{{ article.safe_title}}".</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
        "new_value": '<p>Dear editors,</p><p>This is an automatic notification to inform you that Typesetting is complete for article "{{ article.safe_title_html}}".</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    },
    ("email", "typesetting_proofreader_completed"): {
        "old_value": "<p>Dear {{assignment.manager.salutation_name}},</p><p>This is a notification to let you know that the proofing you requested for the article {{assignment.round.article.safe_title}}, with article number {{assignment.round.article.pk}}, has now been completed by {{assignment.proofreader.full_name}}.</p><p>Best wishes,</p>",
        "new_value": "<p>Dear {{assignment.manager.salutation_name}},</p><p>This is a notification to let you know that the proofing you requested for the article {{assignment.round.article.safe_title_html}}, with article number {{assignment.round.article.pk}}, has now been completed by {{assignment.proofreader.full_name}}.</p><p>Best wishes,</p>",
    },
    ("email", "typesetting_proofreader_cancelled"): {
        "old_value": "<p>Dear {{assignment.proofreader.salutation_name}},</p><p>This is a notification to let you know that your proofreading request for the article {{assignment.round.article.safe_title}}, with article number {{assignment.round.article.pk}} has been cancelled. This means that you no longer need to complete this proofreading task</p><p>Best wishes,</p><p>{{ assignment.manager.signature|safe }}</p>",
        "new_value": "<p>Dear {{assignment.proofreader.salutation_name}},</p><p>This is a notification to let you know that your proofreading request for the article {{assignment.round.article.safe_title_html}}, with article number {{assignment.round.article.pk}} has been cancelled. This means that you no longer need to complete this proofreading task</p><p>Best wishes,</p><p>{{ assignment.manager.signature|safe }}</p>",
    },
    ("email", "typesetting_proofreader_reset"): {
        "old_value": "<p>Dear {{assignment.proofreader.salutation_name}},</p><p>This is a notification to let you know that your proofreading request for the article {{assignment.round.article.safe_title}}, with article number {{assignment.round.article.pk}}, has been reopened. Please log in to the journal using this link in order to complete this proofreading request: {{ typesetting_proofreading_assignments }}.</p><p>Thank you for your help,</p><p>Best wishes,</p><p>{{ assignment.manager.signature|safe }}</p>",
        "new_value": "<p>Dear {{assignment.proofreader.salutation_name}},</p><p>This is a notification to let you know that your proofreading request for the article {{assignment.round.article.safe_title_html}}, with article number {{assignment.round.article.pk}}, has been reopened. Please log in to the journal using this link in order to complete this proofreading request: {{ typesetting_proofreading_assignments }}.</p><p>Thank you for your help,</p><p>Best wishes,</p><p>{{ assignment.manager.signature|safe }}</p>",
    },
    ("email", "typesetting_typesetter_cancelled"): {
        "old_value": "<p>Dear {{assignment.proofreader.salutation_name}},</p><p>This is a notification to let you know that your typesetting request for the article {{assignment.round.article.safe_title}}, with article number {{assignment.round.article.pk}}, has been cancelled. This means that you no longer need to complete this task.</p><p>Thank you for your help,</p><p>{{ assignment.manager.signature|safe }}</p>",
        "new_value": "<p>Dear {{assignment.proofreader.salutation_name}},</p><p>This is a notification to let you know that your typesetting request for the article {{assignment.round.article.safe_title_html}}, with article number {{assignment.round.article.pk}}, has been cancelled. This means that you no longer need to complete this task.</p><p>Thank you for your help,</p><p>{{ assignment.manager.signature|safe }}</p>",
    },
    ("email", "typesetting_typesetter_deleted"): {
        "old_value": "<p>Dear {{assignment.proofreader.salutation_name}},</p><p>This is a notification to let you know that your typesetting request for the article {{assignment.round.article.safe_title}}, with article number {{assignment.round.article.pk}}, has been deleted. This means that you no longer need to complete this task.</p><p>Thank you for your help,</p><p>{{ assignment.manager.signature|safe }}</p>",
        "new_value": "<p>Dear {{assignment.proofreader.salutation_name}},</p><p>This is a notification to let you know that your typesetting request for the article {{assignment.round.article.safe_title_html}}, with article number {{assignment.round.article.pk}}, has been deleted. This means that you no longer need to complete this task.</p><p>Thank you for your help,</p><p>{{ assignment.manager.signature|safe }}</p>",
    },
    ("email", "review_decision_desk_reject"): {
        "old_value": '<p>Dear {{ article.correspondence_author.full_name|se_can_see_pii:article }}</p><p>Thank you for submitting your manuscript "{{ article.safe_title }}" to {{ article.journal.name }}. After careful consideration, we regret to inform you that your submission has not been selected for peer review.</p><p>We appreciate the opportunity to consider your work.</p><p>Regards,</p>{{ request.user.signature|safe }}',
        "new_value": '<p>Dear {{ article.correspondence_author.full_name|se_can_see_pii:article }}</p><p>Thank you for submitting your manuscript "{{ article.safe_title_html }}" to {{ article.journal.name }}. After careful consideration, we regret to inform you that your submission has not been selected for peer review.</p><p>We appreciate the opportunity to consider your work.</p><p>Regards,</p>{{ request.user.signature|safe }}',
    },
}


def replace_values(apps, schema_editor):
    for key, values in SETTINGS_TO_UPDATE.items():
        group, name = key
        old_value = values["old_value"]
        new_value = values["new_value"]
        migration_utils.update_default_setting_values(
            apps,
            setting_name=name,
            group_name=group,
            values_to_replace=[old_value],
            replacement_value=new_value,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0043_logentry_actor_email_alter_logentry_ip_address"),
    ]

    operations = [
        migrations.RunPython(
            replace_values,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
