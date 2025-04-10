# Guide to contributing developer documentation

We want it to be easy to contribute to Janeway. With that in mind, Janeway developer documentation should be accessible, helpful, and consistent.

> [!NOTE]
> End-user documentation is now a separate thing. See [openlibhums/memory-alpha](https://github.com/openlibhums/memory-alpha/tree/main/content/support)

## Main style guide

We follow the [Google developer documentation style guide](https://developers.google.com/style/). If something is covered in the Google guide, we only mention it on this page if we want to highlight it (like with accessibility), or we want to make an exception (like with British spelling).

## Accessibility

We want to include people, not exclude them. So write documentation with accessibility in mind. Images should have text alternatives, links should be contextual, and colour alone should not be used to convey information. Images should only be used when text cannot. For example, a table should be written in Markdown and not pasted in as an image, but an image is appropriate for a screenshot. Similarly consider using [Mermaid (written accessibly)](https://mermaid.js.org/config/accessibility.html) for diagrams.

> [!NOTE]
> Many more [guidelines for accessibility are laid out in the Google developer guide](https://developers.google.com/style/accessibility).

## Readability and structure

Make your document easy to read by using contextual headings (levels h1-h6 using Markdown has syntax `#`).

Use short paragraphs and consider using list markup where appropriate.

> [!NOTE]
> See also the Google guide sections on [jargon](https://developers.google.com/style/jargon), [prescriptive documentation](https://developers.google.com/style/prescriptive-documentation), and [voice and tone](https://developers.google.com/style/tone).

## Audience

Our docs may be read by people with varying familiarity with our technology. When you write a new piece of documentation, think about who is most likely to try to read it.

* What is their main goal?
* What do they know already?
* What do they most likely _not_ know?

Anything the reader must know before they can understand your writing is prior knowledge. If you can distil the prior knowledge into a sentence, put that at the top of your documentation. Some examples:

* "Most of our developer guides assume you know Python and can use the Unix command line."

* "In this guide to the custom styling plugin, we assume you know the basics of Cascading Style Sheets (CSS), including selectors, specificity, and text formatting rules."

> [!NOTE]
> See ["Writing for a global audience"](https://developers.google.com/style/translation) in the Google guide.

## Context

Don’t just give the reader information. Help them understand things they may not know about Janeway that may be relevant to their goal.

In your experience, what crucial context about Janeway do people need when first doing the thing you’re documenting? Don't assume they've read other parts of the documentation. Cross-reference other pages where appropriate. Some examples:

* "Janeway supports PostgreSQL, MySQL, and SQLite."

* "If you are not familiar with Janeway plugins, you may want to read our [plugin guide](/plugin/guide)."

* "User-entered rich text is sanitized with [Python bleach](/bleach/settings), so iframe embeds cannot be used in site content."

You can format these as [GitHub Markdown "alerts" if you like](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts).

Also think about how new pages fit into existing documentation, and add cross-references elsewhere to help people find the new material.

## Spelling

We are centred in the UK, so we adopt British spelling in all user-facing writing, taking the first variant listed in the [Oxford English Dictionary](https://www.oed.com/dictionary/centre_n1) when in doubt.

However, for much of our code, we use American spelling for consistency with a third party, like CSS `color` or Creative Commons `license`.
