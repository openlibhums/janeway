---

last_updated: 2025-04-09
last_updated_by: joemull

---

# Guide to contributing developer documentation

We want it to be easy to contribute to Janeway. With that in mind, Janeway
developer documentation should be helpful, up to date, and consistent.

> [!NOTE]
> End-user documentation is now a separate thing.
> See [openlibhums/memory-alpha](https://github.com/openlibhums/memory-alpha/tree/main/content/support)

## Audience

Our docs may be read by people with varying familiarity with our technology.
When you write a new piece of documentation, think about who is most likely to
try to read it.

* What is their main goal?
* What do they know already?
* What do they most likely _not_ know?

Anything the reader must know before they can understand your writing is prior
knowledge. If you can distil the prior knowledge into a sentence, put that at
the top of your documentation. Some examples:

* "Most of our developer guides assume you know Python and can use the Unix command line."

* "In this guide to the custom styling plugin, we assume you know the basics of
  Cascading Style Sheets (CSS), including selectors, specificity, and text
  formatting rules."

## Context

Don’t just give the reader information. Help them understand things they may
not know about Janeway that may be relevant to their goal.

In your experience, what crucial context about Janeway do people need when
first doing the thing you’re documenting? Don't assume they've read other
parts of the documentation. Cross-reference other pages where appropriate.
Some examples:

* "Janeway supports PostgreSQL, MySQL, and SQLite."

* "If you are not familiar with Janeway plugins, you may want to read our
  [plugin guide](/plugin/guide)."

* "User-entered rich text is sanitized with [Python
  bleach](/bleach/settings), so iframe embeds cannot be used in site content."

You can format these as [GitHub Markdown "alerts" if you
like](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts).

## Keeping things up to date

We will most likely use a YAML frontmatter block to keep track of key info at the
top of each article.

We will use this spot to record who last gave the page a comprehensive
update, and when, so we can keep track of which pages need attention at regular
intervals.

The person in `last_updated_by` is not an indication that that person must keep
the page up to date. It is just helpful context for future authors.

```yaml
last_updated: YYYY-MM-DD
last_updated_by: githubusername
```

## Style

We follow the [Google developer documentation style
guide](https://developers.google.com/style/). We are centred in the UK, so we
default to British spelling, taking the first variant listed in the [Oxford
English Dictionary](https://www.oed.com/dictionary/centre_n1) when in doubt,
except for places where we have to use American spelling for consistency with
a third party, like CSS "color" or Creative Commons "license".
