# Janeway Accessibility Conformance

Janeway is moving towards compliance with WCAG 2.2 AA.  This process has started with the Front of House. Next will come the back office, and then the plugins. Version tested is given as the git commit reference on the master branch.

## Results Key

| Result | Markdown Symbol |
|---|---|
| Not applicable | :brown_square: `:brown_square:` |
| Partially supports | :orange_circle: `:orange_circle:` |
| Supports | :white_check_mark: `:white_check_mark:` |
| Does not support | :x: `:x:` |

## Front of House - OLH Theme

| Result               | Success Criterion                                            | Level | Conformance        | Remarks | Audit                | Version    |
|---|---|---|---|---|---|---|
|                      | 1.1.1 Non-text Content                                       | A     |                    |         |                      |            |
| :brown_square:       | 1.2.1 Audio-only and Video-only (Prerecorded)                | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5085) | f23d166d8  |
| :brown_square:       | 1.2.2 Captions (Prerecorded)                                 | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5086) | f23d166d8  |
| :brown_square:       | 1.2.3 Audio Description or Media Alternative (Prerecorded)   | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5087) | f23d166d8  |
| :brown_square:       | 1.2.4 Captions (Live)                                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5088) | f23d166d8  |
| :brown_square:       | 1.2.5 Audio Description (Prerecorded)                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5089) | f23d166d8  |
|                      | 1.3.1 Info and Relationships                                 | A     |                    |         |                      |            |
| :white_check_mark:   | 1.3.2 Meaningful Sequence                                    | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5051) | f23d166d8  |
| :orange_circle:      | 1.3.3 Sensory Characteristics                                | A     | Partially supports | toastr.js close buttons do not have text. | [January 2026](https://github.com/openlibhums/janeway/issues/5105) | f23d166d8  |
| :orange_circle:      | 1.3.4 Orientation                                            | AA    | Partially supports | Bugs on portrait/mobile, see audit. | [March 2026](https://github.com/openlibhums/janeway/issues/5108) | f23d166d8  |
|                      | 1.3.5 Identify Input Purpose                                 | AA    |                    |         |                      |            |
| :white_check_mark:   | 1.4.1 Use of Color                                           | A     | Supports           |         | [March 2026](https://github.com/openlibhums/janeway/issues/5114) | f23d166d8  |
|                      | 1.4.10 Reflow                                                | AA    |                    |         |                      |            |
|                      | 1.4.11 Non-text Contrast                                     | AA    |                    |         |                      |            |
| :orange_circle:      | 1.4.12 Text Spacing                                          | AA    | Partially supports | a few isolated bugs | [January 2026](https://github.com/openlibhums/janeway/issues/5120) | f23d166d8  |
|                      | 1.4.13 Content on Hover or Focus                             | AA    |                    |         |                      |            |
| :brown_square:       | 1.4.2 Audio Control                                          | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5090) | f23d166d8  |
|                      | 1.4.3 Contrast (Minimum)                                     | AA    |                    |         |                      |            |
|                      | 1.4.4 Resize Text                                            | AA    |                    |         |                      |            |
| :white_check_mark:   | 1.4.5 Images of Text                                         | AA    | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5099) | f23d166d8  |
|                      | 2.1.1 Keyboard                                               | A     |                    |         |                      |            |
|                      | 2.1.2 No Keyboard Trap                                       | A     |                    |         |                      |            |
| :brown_square:       | 2.1.4 Character Key Shortcuts                                | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5091) | f23d166d8  |
| :orange_circle:      | 2.2.1 Timing Adjustable                                      | A     | Partially supports | Log-out message cannot be paused. | [February 2026](https://github.com/openlibhums/janeway/issues/5144) | f23d166d8  |
| :brown_square:       | 2.2.2 Pause, Stop, Hide                                      | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5145) | f23d166d8  |
| :white_check_mark:   | 2.3.1 Three Flashes or Below Threshold                       | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5147) | f23d166d8  |
| :white_check_mark:   | 2.4.1 Bypass Blocks                                          | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5101) | f23d166d8  |
|                      | 2.4.11 Focus Not Obscured (Minimum)                          | AA    |                    |         |                      |            |
| :orange_circle:      | 2.4.2 Page Titled                                            | A     | Partially supports | All have titles, but they are not fully descriptive. | [February 2026](https://github.com/openlibhums/janeway/issues/5146) | f23d166d8  |
|                      | 2.4.3 Focus Order                                            | A     |                    |         |                      |            |
|                      | 2.4.4 Link Purpose (In Context)                              | A     |                    |         |                      |            |
| :orange_circle:      | 2.4.5 Multiple Ways                                          | AA    | Partially supports |         | [Feburary 2026](https://github.com/openlibhums/janeway/issues/5150) | f23d166d8  |
|                      | 2.4.6 Headings and Labels                                    | AA    |                    |         |                      |            |
|                      | 2.4.7 Focus Visible                                          | AA    |                    |         |                      |            |
| :white_check_mark:   | 2.5.1 Pointer Gestures                                       | A     | Supports           |         | [Feburary 2026](https://github.com/openlibhums/janeway/issues/5154) | f23d166d8  |
| :brown_square:       | 2.5.2 Pointer Cancellation                                   | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5092) | f23d166d8  |
|                      | 2.5.3 Label in Name                                          | A     |                    |         |                      |            |
| :brown_square:       | 2.5.4 Motion Actuation                                       | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5093) | f23d166d8  |
| :brown_square:       | 2.5.7 Dragging Movements                                     | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5094) | f23d166d8  |
|                      | 2.5.8 Target Size (Minimum)                                  | AA    |                    |         |                      |            |
| :orange_circle:      | 3.1.1 Language of Page                                       | A     | Partially supports | Single bug in article print page. | [February 2026](https://github.com/openlibhums/janeway/issues/5157) | f23d166d8  |
| :white_check_mark:   | 3.1.2 Language of Parts                                      | AA    | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5158) | f23d166d8  |
|                      | 3.2.1 On Focus                                               | A     |                    |         |                      |            |
|                      | 3.2.2 On Input                                               | A     |                    |         |                      |            |
| :orange_circle:      | 3.2.3 Consistent Navigation                                  | AA    | Partially supports | Single urgent bugfix on mobile | [February 2026](https://github.com/openlibhums/janeway/issues/5161) | f23d166d8  |
|                      | 3.2.4 Consistent Identification                              | AA    |                    |         |                      |            |
| :white_check_mark:   | 3.2.6 Consistent Help                                        | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5163) | f23d166d8  |
| :white_check_mark:   | 3.3.1 Error Identification                                   | A     | Supports           |         | [March 2026](https://github.com/openlibhums/janeway/issues/5164) | f23d166d8  |
|                      | 3.3.2 Labels or Instructions                                 | A     |                    |         |                      |            |
| :white_check_mark:   | 3.3.3 Error Suggestion                                       | AA    | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5166) | f23d166d8  |
| :brown_square:       | 3.3.4 Error Prevention (Legal, Financial, Data)              | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5095) | f23d166d8  |
| :brown_square:       | 3.3.7 Redundant Entry                                        | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5096) | f23d166d8  |
| :brown_square:       | 3.3.8 Accessible Authentication (Minimum)                    | AA    | Not applicable     |         | [February 2026](https://github.com/openlibhums/janeway/issues/5167) | f23d166d8  |
|                      | 4.1.2 Name, Role, Value                                      | A     |                    |         |                      |            |
| :brown_square:       | 4.1.3 Status Messages                                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5097) | f23d166d8  |

## Front of House - Material Theme

| Result               | Success Criterion                                            | Level | Conformance        | Remarks | Audit                | Version    |
|---|---|---|---|---|---|---|
|                      | 1.1.1 Non-text Content                                       | A     |                    |         |                      |            |
| :brown_square:       | 1.2.1 Audio-only and Video-only (Prerecorded)                | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5085) | f23d166d8  |
| :brown_square:       | 1.2.2 Captions (Prerecorded)                                 | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5086) | f23d166d8  |
| :brown_square:       | 1.2.3 Audio Description or Media Alternative (Prerecorded)   | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5087) | f23d166d8  |
| :brown_square:       | 1.2.4 Captions (Live)                                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5088) | f23d166d8  |
| :brown_square:       | 1.2.5 Audio Description (Prerecorded)                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5089) | f23d166d8  |
|                      | 1.3.1 Info and Relationships                                 | A     |                    |         |                      |            |
| :white_check_mark:   | 1.3.2 Meaningful Sequence                                    | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5051) | f23d166d8  |
| :white_check_mark:   | 1.3.3 Sensory Characteristics                                | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5105) | f23d166d8  |
| :orange_circle:      | 1.3.4 Orientation                                            | AA    | Partially supports | Not responsive on iOS Safari. Incompatible with wide header images. | [March 2026](https://github.com/openlibhums/janeway/issues/5108) | f23d166d8  |
|                      | 1.3.5 Identify Input Purpose                                 | AA    |                    |         |                      |            |
| :white_check_mark:   | 1.4.1 Use of Color                                           | A     | Supports           |         | [March 2026](https://github.com/openlibhums/janeway/issues/5114) | f23d166d8  |
|                      | 1.4.10 Reflow                                                | AA    |                    |         |                      |            |
|                      | 1.4.11 Non-text Contrast                                     | AA    |                    |         |                      |            |
| :x:                  | 1.4.12 Text Spacing                                          | AA    | Does not support   | Desktop navigation is unusable at increased spacing. | [January 2026](https://github.com/openlibhums/janeway/issues/5120) | f23d166d8  |
|                      | 1.4.13 Content on Hover or Focus                             | AA    |                    |         |                      |            |
| :brown_square:       | 1.4.2 Audio Control                                          | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5090) | f23d166d8  |
|                      | 1.4.3 Contrast (Minimum)                                     | AA    |                    |         |                      |            |
|                      | 1.4.4 Resize Text                                            | AA    |                    |         |                      |            |
| :white_check_mark:   | 1.4.5 Images of Text                                         | AA    | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5099) | f23d166d8  |
|                      | 2.1.1 Keyboard                                               | A     |                    |         |                      |            |
|                      | 2.1.2 No Keyboard Trap                                       | A     |                    |         |                      |            |
| :brown_square:       | 2.1.4 Character Key Shortcuts                                | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5091) | f23d166d8  |
| :orange_circle:      | 2.2.1 Timing Adjustable                                      | A     | Partially supports | Carousel and log-out message cannot be paused. | [February 2026](https://github.com/openlibhums/janeway/issues/5144) | f23d166d8  |
| :orange_circle:      | 2.2.2 Pause, Stop, Hide                                      | A     | Partially supports | Carousel autoplays and cannot be paused. | [January 2026](https://github.com/openlibhums/janeway/issues/5145) | f23d166d8  |
| :white_check_mark:   | 2.3.1 Three Flashes or Below Threshold                       | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5147) | f23d166d8  |
| :white_check_mark:   | 2.4.1 Bypass Blocks                                          | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5101) | f23d166d8  |
|                      | 2.4.11 Focus Not Obscured (Minimum)                          | AA    |                    |         |                      |            |
| :orange_circle:      | 2.4.2 Page Titled                                            | A     | Partially supports | All have titles, but they are not fully descriptive. | [February 2026](https://github.com/openlibhums/janeway/issues/5146) | f23d166d8  |
|                      | 2.4.3 Focus Order                                            | A     |                    |         |                      |            |
|                      | 2.4.4 Link Purpose (In Context)                              | A     |                    |         |                      |            |
| :orange_circle:      | 2.4.5 Multiple Ways                                          | AA    | Partially supports |         | [Feburary 2026](https://github.com/openlibhums/janeway/issues/5150) | f23d166d8  |
|                      | 2.4.6 Headings and Labels                                    | AA    |                    |         |                      |            |
|                      | 2.4.7 Focus Visible                                          | AA    |                    |         |                      |            |
| :white_check_mark:   | 2.5.1 Pointer Gestures                                       | A     | Supports           |         | [Feburary 2026](https://github.com/openlibhums/janeway/issues/5154) | f23d166d8  |
| :brown_square:       | 2.5.2 Pointer Cancellation                                   | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5092) | f23d166d8  |
|                      | 2.5.3 Label in Name                                          | A     |                    |         |                      |            |
| :brown_square:       | 2.5.4 Motion Actuation                                       | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5093) | f23d166d8  |
| :brown_square:       | 2.5.7 Dragging Movements                                     | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5094) | f23d166d8  |
|                      | 2.5.8 Target Size (Minimum)                                  | AA    |                    |         |                      |            |
| :white_check_mark:   | 3.1.1 Language of Page                                       | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5157) | f23d166d8  |
| :white_check_mark:   | 3.1.2 Language of Parts                                      | AA    | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5158) | f23d166d8  |
|                      | 3.2.1 On Focus                                               | A     |                    |         |                      |            |
|                      | 3.2.2 On Input                                               | A     |                    |         |                      |            |
| :white_check_mark:   | 3.2.3 Consistent Navigation                                  | AA    | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5161) | f23d166d8  |
|                      | 3.2.4 Consistent Identification                              | AA    |                    |         |                      |            |
| :white_check_mark:   | 3.2.6 Consistent Help                                        | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5163) | f23d166d8  |
| :white_check_mark:   | 3.3.1 Error Identification                                   | A     | Supports           |         | [March 2026](https://github.com/openlibhums/janeway/issues/5164) | f23d166d8  |
|                      | 3.3.2 Labels or Instructions                                 | A     |                    |         |                      |            |
| :white_check_mark:   | 3.3.3 Error Suggestion                                       | AA    | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5166) | f23d166d8  |
| :brown_square:       | 3.3.4 Error Prevention (Legal, Financial, Data)              | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5095) | f23d166d8  |
| :brown_square:       | 3.3.7 Redundant Entry                                        | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5096) | f23d166d8  |
| :brown_square:       | 3.3.8 Accessible Authentication (Minimum)                    | AA    | Not applicable     |         | [February 2026](https://github.com/openlibhums/janeway/issues/5167) | f23d166d8  |
|                      | 4.1.2 Name, Role, Value                                      | A     |                    |         |                      |            |
| :brown_square:       | 4.1.3 Status Messages                                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5097) | f23d166d8  |

## Front of House - Clean Theme

| Result               | Success Criterion                                            | Level | Conformance        | Remarks | Audit                | Version    |
|---|---|---|---|---|---|---|
| :orange_circle:      | 1.1.1 Non-text Content                                       | A     | Partially supports |         | June 2024 VPAT       |            |
| :brown_square:       | 1.2.1 Audio-only and Video-only (Prerecorded)                | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5085) | f23d166d8  |
| :brown_square:       | 1.2.2 Captions (Prerecorded)                                 | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5086) | f23d166d8  |
| :brown_square:       | 1.2.3 Audio Description or Media Alternative (Prerecorded)   | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5087) | f23d166d8  |
| :brown_square:       | 1.2.4 Captions (Live)                                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5088) | f23d166d8  |
| :brown_square:       | 1.2.5 Audio Description (Prerecorded)                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5089) | f23d166d8  |
| :orange_circle:      | 1.3.1 Info and Relationships                                 | A     | Partially supports |         | June 2024 VPAT       |            |
| :white_check_mark:   | 1.3.2 Meaningful Sequence                                    | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5051) | f23d166d8  |
| :white_check_mark:   | 1.3.3 Sensory Characteristics                                | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5105) | f23d166d8  |
| :orange_circle:      | 1.3.4 Orientation                                            | AA    | Partially supports | Bug in (portrait) carousel for long titles. | [March 2026](https://github.com/openlibhums/janeway/issues/5108) | f23d166d8  |
| :brown_square:       | 1.3.5 Identify Input Purpose                                 | AA    | Not applicable     |         | June 2024 VPAT       |            |
| :white_check_mark:   | 1.4.1 Use of Color                                           | A     | Supports           |         | [March 2026](https://github.com/openlibhums/janeway/issues/5114) | f23d166d8  |
| :white_check_mark:   | 1.4.10 Reflow                                                | AA    | Supports           |         | June 2024 VPAT       |            |
| :brown_square:       | 1.4.11 Non-text Contrast                                     | AA    | Not applicable     | Colour themes are defined by users. | June 2024 VPAT       |            |
| :orange_circle:      | 1.4.12 Text Spacing                                          | AA    | Partially supports | a few isolated bugs | [January 2026](https://github.com/openlibhums/janeway/issues/5120) | f23d166d8  |
| :orange_circle:      | 1.4.13 Content on Hover or Focus                             | AA    | Partially supports |         | June 2024 VPAT       |            |
| :brown_square:       | 1.4.2 Audio Control                                          | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5090) | f23d166d8  |
| :brown_square:       | 1.4.3 Contrast (Minimum)                                     | AA    | Not applicable     | Colour themes are defined by users. | June 2024 VPAT       |            |
| :orange_circle:      | 1.4.4 Resize Text                                            | AA    | Partially supports |         | June 2024 VPAT       |            |
| :white_check_mark:   | 1.4.5 Images of Text                                         | AA    | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5099) | f23d166d8  |
| :white_check_mark:   | 2.1.1 Keyboard                                               | A     | Supports           |         | June 2024 VPAT       |            |
| :orange_circle:      | 2.1.2 No Keyboard Trap                                       | A     | Partially supports |         | June 2024 VPAT       |            |
| :brown_square:       | 2.1.4 Character Key Shortcuts                                | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5091) | f23d166d8  |
| :white_check_mark:   | 2.2.1 Timing Adjustable                                      | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5144) | f23d166d8  |
| :white_check_mark:   | 2.2.2 Pause, Stop, Hide                                      | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5145) | f23d166d8  |
| :white_check_mark:   | 2.3.1 Three Flashes or Below Threshold                       | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5147) | f23d166d8  |
| :white_check_mark:   | 2.4.1 Bypass Blocks                                          | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5101) | f23d166d8  |
| :white_check_mark:   | 2.4.11 Focus Not Obscured (Minimum)                          | AA    | Supports           |         | June 2024 VPAT       |            |
| :orange_circle:      | 2.4.2 Page Titled                                            | A     | Partially supports | All have titles, but they are not fully descriptive. | [February 2026](https://github.com/openlibhums/janeway/issues/5146) | f23d166d8  |
| :orange_circle:      | 2.4.3 Focus Order                                            | A     | Partially supports |         | June 2024 VPAT       |            |
| :orange_circle:      | 2.4.4 Link Purpose (In Context)                              | A     | Partially supports |         | June 2024 VPAT       |            |
| :orange_circle:      | 2.4.5 Multiple Ways                                          | AA    | Partially supports |         | [Feburary 2026](https://github.com/openlibhums/janeway/issues/5150) | f23d166d8  |
| :orange_circle:      | 2.4.6 Headings and Labels                                    | AA    | Partially supports |         | June 2024 VPAT       |            |
| :white_check_mark:   | 2.4.7 Focus Visible                                          | AA    | Supports           |         | June 2024 VPAT       |            |
| :white_check_mark:   | 2.5.1 Pointer Gestures                                       | A     | Supports           |         | [Feburary 2026](https://github.com/openlibhums/janeway/issues/5154) | f23d166d8  |
| :brown_square:       | 2.5.2 Pointer Cancellation                                   | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5092) | f23d166d8  |
| :white_check_mark:   | 2.5.3 Label in Name                                          | A     | Supports           |         | June 2024 VPAT       |            |
| :brown_square:       | 2.5.4 Motion Actuation                                       | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5093) | f23d166d8  |
| :brown_square:       | 2.5.7 Dragging Movements                                     | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5094) | f23d166d8  |
| :orange_circle:      | 2.5.8 Target Size (Minimum)                                  | AA    | Partially supports |         | June 2024 VPAT       |            |
| :orange_circle:      | 3.1.1 Language of Page                                       | A     | Partially supports | Single bug in article print page. | [February 2026](https://github.com/openlibhums/janeway/issues/5157) | f23d166d8  |
| :white_check_mark:   | 3.1.2 Language of Parts                                      | AA    | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5158) | f23d166d8  |
| :orange_circle:      | 3.2.1 On Focus                                               | A     | Partially supports |         | June 2024 VPAT       |            |
| :orange_circle:      | 3.2.2 On Input                                               | A     | Partially supports |         | June 2024 VPAT       |            |
| :white_check_mark:   | 3.2.3 Consistent Navigation                                  | AA    | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5161) | f23d166d8  |
| :white_check_mark:   | 3.2.4 Consistent Identification                              | AA    | Supports           |         | June 2024 VPAT       |            |
| :white_check_mark:   | 3.2.6 Consistent Help                                        | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5163) | f23d166d8  |
| :white_check_mark:   | 3.3.1 Error Identification                                   | A     | Supports           |         | [March 2026](https://github.com/openlibhums/janeway/issues/5164) | f23d166d8  |
| :orange_circle:      | 3.3.2 Labels or Instructions                                 | A     | Partially supports |         | June 2024 VPAT       |            |
| :white_check_mark:   | 3.3.3 Error Suggestion                                       | AA    | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5166) | f23d166d8  |
| :brown_square:       | 3.3.4 Error Prevention (Legal, Financial, Data)              | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5095) | f23d166d8  |
| :brown_square:       | 3.3.7 Redundant Entry                                        | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5096) | f23d166d8  |
| :brown_square:       | 3.3.8 Accessible Authentication (Minimum)                    | AA    | Not applicable     |         | [February 2026](https://github.com/openlibhums/janeway/issues/5167) | f23d166d8  |
| :orange_circle:      | 4.1.2 Name, Role, Value                                      | A     | Partially supports |         | June 2024 VPAT       |            |
| :brown_square:       | 4.1.3 Status Messages                                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5097) | f23d166d8  |

## Front of House - Accessibility Mode

Accessibility Mode is provided as an user-selectable alternative from all three themes.

| Result               | Success Criterion                                            | Level | Conformance        | Remarks | Audit                | Version    |
|---|---|---|---|---|---|---|
|                      | 1.1.1 Non-text Content                                       | A     |                    |         |                      |            |
| :brown_square:       | 1.2.1 Audio-only and Video-only (Prerecorded)                | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5085) | f23d166d8  |
| :brown_square:       | 1.2.2 Captions (Prerecorded)                                 | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5086) | f23d166d8  |
| :brown_square:       | 1.2.3 Audio Description or Media Alternative (Prerecorded)   | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5087) | f23d166d8  |
| :brown_square:       | 1.2.4 Captions (Live)                                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5088) | f23d166d8  |
| :brown_square:       | 1.2.5 Audio Description (Prerecorded)                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5089) | f23d166d8  |
|                      | 1.3.1 Info and Relationships                                 | A     |                    |         |                      |            |
| :white_check_mark:   | 1.3.2 Meaningful Sequence                                    | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5051) | f23d166d8  |
| :white_check_mark:   | 1.3.3 Sensory Characteristics                                | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5105) | f23d166d8  |
|                      | 1.3.4 Orientation                                            | AA    |                    |         |                      |            |
|                      | 1.3.5 Identify Input Purpose                                 | AA    |                    |         |                      |            |
|                      | 1.4.1 Use of Color                                           | A     |                    |         |                      |            |
|                      | 1.4.10 Reflow                                                | AA    |                    |         |                      |            |
|                      | 1.4.11 Non-text Contrast                                     | AA    |                    |         |                      |            |
|                      | 1.4.12 Text Spacing                                          | AA    |                    |         |                      |            |
|                      | 1.4.13 Content on Hover or Focus                             | AA    |                    |         |                      |            |
| :brown_square:       | 1.4.2 Audio Control                                          | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5090) | f23d166d8  |
|                      | 1.4.3 Contrast (Minimum)                                     | AA    |                    |         |                      |            |
|                      | 1.4.4 Resize Text                                            | AA    |                    |         |                      |            |
| :white_check_mark:   | 1.4.5 Images of Text                                         | AA    | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5099) | f23d166d8  |
|                      | 2.1.1 Keyboard                                               | A     |                    |         |                      |            |
|                      | 2.1.2 No Keyboard Trap                                       | A     |                    |         |                      |            |
| :brown_square:       | 2.1.4 Character Key Shortcuts                                | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5091) | f23d166d8  |
|                      | 2.2.1 Timing Adjustable                                      | A     |                    |         |                      |            |
|                      | 2.2.2 Pause, Stop, Hide                                      | A     |                    |         |                      |            |
| :white_check_mark:   | 2.3.1 Three Flashes or Below Threshold                       | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5147) | f23d166d8  |
| :white_check_mark:   | 2.4.1 Bypass Blocks                                          | A     | Supports           |         | [January 2026](https://github.com/openlibhums/janeway/issues/5101) | f23d166d8  |
|                      | 2.4.11 Focus Not Obscured (Minimum)                          | AA    |                    |         |                      |            |
|                      | 2.4.2 Page Titled                                            | A     |                    |         |                      |            |
|                      | 2.4.3 Focus Order                                            | A     |                    |         |                      |            |
|                      | 2.4.4 Link Purpose (In Context)                              | A     |                    |         |                      |            |
| :orange_circle:      | 2.4.5 Multiple Ways                                          | AA    | Partially supports |         | [Feburary 2026](https://github.com/openlibhums/janeway/issues/5150) | f23d166d8  |
|                      | 2.4.6 Headings and Labels                                    | AA    |                    |         |                      |            |
|                      | 2.4.7 Focus Visible                                          | AA    |                    |         |                      |            |
|                      | 2.5.1 Pointer Gestures                                       | A     |                    |         |                      |            |
| :brown_square:       | 2.5.2 Pointer Cancellation                                   | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5092) | f23d166d8  |
|                      | 2.5.3 Label in Name                                          | A     |                    |         |                      |            |
| :brown_square:       | 2.5.4 Motion Actuation                                       | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5093) | f23d166d8  |
| :brown_square:       | 2.5.7 Dragging Movements                                     | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5094) | f23d166d8  |
|                      | 2.5.8 Target Size (Minimum)                                  | AA    |                    |         |                      |            |
|                      | 3.1.1 Language of Page                                       | A     |                    |         |                      |            |
|                      | 3.1.2 Language of Parts                                      | AA    |                    |         |                      |            |
|                      | 3.2.1 On Focus                                               | A     |                    |         |                      |            |
|                      | 3.2.2 On Input                                               | A     |                    |         |                      |            |
|                      | 3.2.3 Consistent Navigation                                  | AA    |                    |         |                      |            |
|                      | 3.2.4 Consistent Identification                              | AA    |                    |         |                      |            |
| :white_check_mark:   | 3.2.6 Consistent Help                                        | A     | Supports           |         | [February 2026](https://github.com/openlibhums/janeway/issues/5163) | f23d166d8  |
|                      | 3.3.1 Error Identification                                   | A     |                    |         |                      |            |
|                      | 3.3.2 Labels or Instructions                                 | A     |                    |         |                      |            |
|                      | 3.3.3 Error Suggestion                                       | AA    |                    |         |                      |            |
| :brown_square:       | 3.3.4 Error Prevention (Legal, Financial, Data)              | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5095) | f23d166d8  |
| :brown_square:       | 3.3.7 Redundant Entry                                        | A     | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5096) | f23d166d8  |
| :brown_square:       | 3.3.8 Accessible Authentication (Minimum)                    | AA    | Not applicable     |         | [February 2026](https://github.com/openlibhums/janeway/issues/5167) | f23d166d8  |
|                      | 4.1.2 Name, Role, Value                                      | A     |                    |         |                      |            |
| :brown_square:       | 4.1.3 Status Messages                                        | AA    | Not applicable     |         | [January 2026](https://github.com/openlibhums/janeway/issues/5097) | f23d166d8  |

## Back office

No data. Development focus will turn to back office accessibilty improvements after the front of house is addressed in version 1.9.
