<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:fo="http://www.w3.org/1999/XSL/Format"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:mml="http://www.w3.org/1998/Math/MathML"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  exclude-result-prefixes="xlink mml">
  
  <xsl:output indent="yes"/>

  <xsl:param name="logo">/home/martin/Documents/Programming/meXml/transform/resources/logo.png</xsl:param>

<!-- 
Modifications copyright Martin Paul Eve (https://www.martineve.com) 2013
                                                                   -->

<!-- ============================================================= -->
<!--  MODULE:    XSL-FO Preview of Journal Publishing 3.0 XML      -->
<!--  VERSION:   1.0                                               -->
<!--  DATE:      August 2013                                       -->
<!--                                                               -->
<!-- ============================================================= -->

<!-- ============================================================= -->
<!--  SYSTEM:    NCBI Archiving and Interchange Journal Articles   -->
<!--                                                               -->
<!--  PURPOSE:   Provide an XSL-FO preview of a journal article,   -->
<!--             in a form suitable for formatting into PDF        -->
<!--             for printing and page display.                    -->
<!--                                                               -->
<!--  PROCESSOR DEPENDENCIES:                                      -->
<!--             Tested using Saxon 6.5, Saxon 9.1.0.3             -->
<!--                                                               -->
<!--  COMPONENTS REQUIRED:                                         -->
<!--             1) This stylesheet                                -->
<!--             2) The module xhtml-tables-fo.xsl                 -->
<!--                                                               -->
<!--  INPUT:     An XML document valid to the                      -->
<!--             Journal Publishing 3.0 DTD.                       -->
<!--             (And note further assumptions and limitations     -->
<!--             below.)                                           -->
<!--                                                               -->
<!--  OUTPUT:    XSL-FO. Uses XSL-FO 1.1 features; tested with     -->
<!--             AntennaHouse 4.3 with MathML support.             -->
<!--                                                               -->
<!--  ORGANIZATION OF THIS STYLESHEET:                             -->
<!--             TOP-LEVEL PARAMETERS                              -->
<!--             KEYS FOR ID AND RID                               -->
<!--             TYPOGRAPHIC SPECIFICATIONS                        -->
<!--               Attribute sets                                  -->
<!--             TOP-LEVEL TEMPLATES                               -->
<!--             METADATA PROCESSING                               -->
<!--               Named templates for metadata processing         -->
<!--             SPECIALIZED FRONT PAGE TEMPLATES                  -->
<!--               Mode "cover-page"                               -->
<!--             DEFAULT TEMPLATES (mostly in no mode)             -->
<!--               Titles                                          -->
<!--               Figures, lists and block-level objects          -->
<!--               Tables                                          -->
<!--               Inline elements                                 -->
<!--               Back matter                                     -->
<!--               Floats group                                    -->
<!--               Citation content                                -->
<!--               Footnotes and cross-references                  -->
<!--               Mode "format"                                   -->
<!--               Mode "label"                                    -->
<!--               Mode "label-text"                               -->
<!--               MathML handling                                 -->
<!--               Writing a name                                  -->
<!--             UTILITY TEMPLATES                                 -->
<!--               Stylesheeet diagnostics                         -->
<!--               Date formatting templates                       -->
<!--               ID assignment                                   -->
<!--             END OF STYLESHEET                                 -->
<!--                                                               -->
<!--  CREATED FOR:                                                 -->
<!--             Digital Archive of Journal Articles               -->
<!--             National Center for Biotechnology Information     -->
<!--                (NCBI)                                         -->
<!--             National Library of Medicine (NLM)                -->
<!--                                                               -->
<!--  CREATED BY:                                                  -->
<!--             Wendell Piez (based on PDF design by              -->
<!--             Kate Hamilton and Debbie Lapeyre, 2004),          -->
<!--             Mulberry Technologies, Inc.                       -->
<!--                                                               -->

<!-- ============================================================= -->
<!--             CHANGE HISTORY                                    -->
<!-- =============================================================

Reason/Occasion                            (who) vx.x (yyyy-mm-dd)
  
                                           (wap) v1.0 (2009-12-08)
 3. In template matching 'fn-group/fn | author-notes/fn' in
   'label-text' mode, added conditional to declaration of variable
   'auto-number-fn' setting to false() when the fn has its own 
   label or @symbol (irrespective of the content of xref elements)

 2. Significant improvement to the logic of template 'fn-xref'
    determining when to create a footnote, vs. only a reference

 1. Added priority '2' to 'main-title' template to avoid match 
    clashes with 'section-title' template over "notes/title"
    (which can also match "back[not(title)]/*/title")

    ============================================================= -->


<!-- ============================================================= -->
<!-- TOP-LEVEL PARAMETERS                                          -->
<!-- ============================================================= -->
<!-- These affect the operation of the stylesheet as a whole. They
     can be overridden at runtime, if desired (use an empty
     string for a false() value), or (better) by an importing
     stylesheet. -->


  <!-- These affect the operation of the stylesheet as a whole. They
     can be overridden at runtime, if desired (use an empty
     string for a false() value), or (better) by an importing
     stylesheet. -->


  <xsl:param name="mathml-support" select="true()"/>
  <!-- If mathml-support is turned off, MathML will be removed from
       the output (while its content is passed through). This allows
       the stylesheet to be used with an XSL-FO engine that does not
       support MathML (while also disabling MathML, of course -->


  <xsl:param name="base-dir" select="false()"/>
  <!-- base-dir specifies the base directory used to evaluate
       relative URIs. If this is left as the default, the 
       formatter will guess as to where graphics are located when 
       relative paths are given.

    For example:
    
    A graphic has <graphic xlink:href="images/babypic.jpg"/>
    base-dir is provided as 'file:///c:/Projects/NLM-data'
    The graphic should be found at
      file:///c:/Projects/NLM-data/images/babypic.jpg

  -->

  
<!-- ============================================================= -->
<!-- KEYS FOR ID AND RID                                           -->
<!-- ============================================================= -->

<xsl:key name="element-by-id" match="*[@id]" use="@id"/>

<xsl:key name="xref-by-rid" match="xref[@rid]" use="@rid"/>


<!-- ============================================================= -->
<!-- TYPOGRAPHIC SPECIFICATIONS                                    -->
<!-- ============================================================= -->

<!-- Most typographical specification is done below by named
     attribute sets, but a few global variables are useful.        -->

<xsl:variable name="mainindent" select="'1pc'"/>

<!-- Font used for Section titles and the like. -->
<xsl:variable name="titlefont">sans-serif</xsl:variable>

<!-- Font used for normal paragraph text.  -->
<xsl:variable name="textfont">DejaVu Sans</xsl:variable>

<!-- Font size for for normal paragraph text and the like. -->
<xsl:variable name="textsize" select="'10pt'"/>
<!-- points -->

<!-- Vertical baseline-to-baseline distance for normal
     paragraph text and the like. -->
<xsl:variable name="textleading" select="'12pt'"/>
<!-- points -->




<!-- ============================================================= -->
<!-- Attribute sets                                                -->
<!-- ============================================================= -->

<xsl:attribute-set name="page-header-title-cell">
  <xsl:attribute name="width">5in</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="page-header-pageno-cell">
  <xsl:attribute name="width">0.5in</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="page-header">
  <xsl:attribute name="font-family">
    <xsl:value-of select="$titlefont"/>
  </xsl:attribute>
  <xsl:attribute name="font-size">9pt</xsl:attribute>
  <xsl:attribute name="line-height">12pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="metadata-line">
  <xsl:attribute name="font-size">8pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="metadata-label">
  <xsl:attribute name="font-family">
    <xsl:value-of select="$titlefont"/>
  </xsl:attribute>
  <xsl:attribute name="keep-with-next.within-page">always</xsl:attribute>
  <xsl:attribute name="font-size">8pt</xsl:attribute>
  <xsl:attribute name="font-weight">bold</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="sans-serif">
  <xsl:attribute name="font-family">sans-serif</xsl:attribute>
  <xsl:attribute name="font-size">85%</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="monospace">
  <xsl:attribute name="font-family">monospace</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="warning" use-attribute-sets="sans-serif">
  <xsl:attribute name="font-style">italic</xsl:attribute>
  <xsl:attribute name="color">darkred</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="generated"/>

<xsl:attribute-set name="data"/>

<xsl:attribute-set name="subscript">
  <xsl:attribute name="vertical-align">sub</xsl:attribute>
  <xsl:attribute name="font-size">60%</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="superscript">
  <xsl:attribute name="vertical-align">super</xsl:attribute>
  <xsl:attribute name="font-size">60%</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="label">
  <xsl:attribute name="keep-with-next.within-page">always</xsl:attribute>
  <xsl:attribute name="font-family">
    <xsl:value-of select="$titlefont"/>
  </xsl:attribute>
  <xsl:attribute name="font-size">9pt</xsl:attribute>
  <xsl:attribute name="font-weight">bold</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="body">
  <xsl:attribute name="margin-left">
    <xsl:value-of select="$mainindent"/>
  </xsl:attribute>
  <xsl:attribute name="font-family">
    <xsl:value-of select="$textfont"/>
  </xsl:attribute>
  <xsl:attribute name="font-size">
    <xsl:value-of select="$textsize"/>
  </xsl:attribute>
  <xsl:attribute name="line-height">
    <xsl:value-of select="$textleading"/>
  </xsl:attribute>
  <xsl:attribute name="text-align">start</xsl:attribute>
  <xsl:attribute name="font-style">normal</xsl:attribute>
  <xsl:attribute name="font-weight">normal</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="back-body">
  <xsl:attribute name="margin-left">
    <xsl:value-of select="$mainindent"/>
  </xsl:attribute>
  <xsl:attribute name="font-family">
    <xsl:value-of select="$textfont"/>
  </xsl:attribute>
  <xsl:attribute name="font-size">
    <xsl:value-of select="$textsize"/>
  </xsl:attribute>
  <xsl:attribute name="line-height">
    <xsl:value-of select="$textleading"/>
  </xsl:attribute>
  <xsl:attribute name="text-align">start</xsl:attribute>
  <xsl:attribute name="font-style">normal</xsl:attribute>
  <xsl:attribute name="font-weight">normal</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="back" use-attribute-sets="back-body">
  <xsl:attribute name="margin-left">0em</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="title">
  <xsl:attribute name="font-family">
    <xsl:value-of select="$titlefont"/>
  </xsl:attribute>
  <xsl:attribute name="keep-with-next.within-page">always</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="main-title" use-attribute-sets="outset title">
  <xsl:attribute name="font-size">14pt</xsl:attribute>
  <xsl:attribute name="line-height">16pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="journal-title" use-attribute-sets="outset title">
  <xsl:attribute name="font-family">
    <xsl:value-of select="$titlefont"/>
  </xsl:attribute>
  <xsl:attribute name="font-size">16pt</xsl:attribute>
  <xsl:attribute name="line-height">18pt</xsl:attribute>
  <xsl:attribute name="color">#ffffff</xsl:attribute>
  <xsl:attribute name="font-style">italic</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="journal-metadata">
  <xsl:attribute name="font-family">
    <xsl:value-of select="$titlefont"/>
  </xsl:attribute>
  <xsl:attribute name="color">#000000</xsl:attribute>
  <xsl:attribute name="keep-with-next.within-page">always</xsl:attribute>
  <xsl:attribute name="font-size">8pt</xsl:attribute>
  <xsl:attribute name="line-height">8pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="section-title" use-attribute-sets="outset title">
  <xsl:attribute name="font-size">12pt</xsl:attribute>
  <xsl:attribute name="line-height">17pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="subsection-title" use-attribute-sets="outset title">
  <xsl:attribute name="font-size">12pt</xsl:attribute>
  <xsl:attribute name="line-height">17pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="block-title" use-attribute-sets="title">
  <xsl:attribute name="font-size">11pt</xsl:attribute>
  <xsl:attribute name="line-height">13pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="subtitle" use-attribute-sets="title">
  <xsl:attribute name="font-size">10pt</xsl:attribute>
  <xsl:attribute name="line-height">12pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="coverpage-heading" use-attribute-sets="panel">
  <xsl:attribute name="font-size">10pt</xsl:attribute>
  <xsl:attribute name="line-height">18pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="panel">
  <xsl:attribute name="space-before">6pt</xsl:attribute>
  <xsl:attribute name="space-after">6pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="abstract" use-attribute-sets="panel"/>

<xsl:attribute-set name="box">
  <xsl:attribute name="border">thin solid black</xsl:attribute>
  <xsl:attribute name="padding">4pt</xsl:attribute>
  <xsl:attribute name="space-before">4pt</xsl:attribute>
  <xsl:attribute name="space-after">4pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="outset">
  <xsl:attribute name="start-indent">0pc</xsl:attribute>
  <!--<xsl:attribute name="start-indent">0pc</xsl:attribute>-->
</xsl:attribute-set>



<xsl:attribute-set name="coverpage-block">
  <xsl:attribute name="space-before">6pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="coverpage-default">
  <xsl:attribute name="font-size">10pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="coverpage" use-attribute-sets="coverpage-default"/>


<xsl:attribute-set name="coverpage-abstract">
  <xsl:attribute name="font-size">10pt</xsl:attribute>
  <xsl:attribute name="text-align">justify</xsl:attribute>
  <xsl:attribute name="space-before">6pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="coverpage-title"
  use-attribute-sets="title coverpage-block">
  <xsl:attribute name="font-size">12pt</xsl:attribute>
  <xsl:attribute name="line-height">17pt</xsl:attribute>
  <xsl:attribute name="space-before">6pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="coverpage-subtitle"
  use-attribute-sets="title coverpage-block">
  <xsl:attribute name="font-size">12pt</xsl:attribute>
  <xsl:attribute name="line-height">16pt</xsl:attribute>
  <xsl:attribute name="space-before">6pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="firstpage-title" use-attribute-sets="title">
  <xsl:attribute name="font-size">14pt</xsl:attribute>
  <xsl:attribute name="line-height">17pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="firstpage-subtitle" use-attribute-sets="title">
  <xsl:attribute name="font-size">12pt</xsl:attribute>
  <xsl:attribute name="line-height">15pt</xsl:attribute>
  <xsl:attribute name="font-style">italic</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="firstpage-alt-title" use-attribute-sets="title">
  <xsl:attribute name="font-size">10pt</xsl:attribute>
  <xsl:attribute name="line-height">15pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="firstpage-trans-title" use-attribute-sets="title">
  <xsl:attribute name="font-size">10pt</xsl:attribute>
  <xsl:attribute name="line-height">15pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="firstpage-trans-subtitle" use-attribute-sets="title">
  <xsl:attribute name="font-size">8pt</xsl:attribute>
  <xsl:attribute name="line-height">15pt</xsl:attribute>
  <xsl:attribute name="font-style">italic</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="section">
  <xsl:attribute name="space-before">12pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="section-metadata" use-attribute-sets="panel"/>

<xsl:attribute-set name="back-section" use-attribute-sets="section"/>

<xsl:attribute-set name="app" use-attribute-sets="section"/>

<xsl:attribute-set name="paragraph">
  <xsl:attribute name="space-before">4pt</xsl:attribute>
  <xsl:attribute name="font-size">11pt</xsl:attribute>
  <xsl:attribute name="line-height">16pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="paragraph-justified">
  <xsl:attribute name="space-before">7pt</xsl:attribute>
  <xsl:attribute name="text-align">justify</xsl:attribute>
  <xsl:attribute name="start-indent">1pc</xsl:attribute>
  <xsl:attribute name="text-indent">1pc</xsl:attribute>
  <xsl:attribute name="font-size">11pt</xsl:attribute>
  <xsl:attribute name="line-height">16pt</xsl:attribute>
  <xsl:attribute name="font-family">
   <xsl:attribute name="font-family">
    <xsl:value-of select="$textfont"/>
  </xsl:attribute></xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="paragraph-justified-noindent">
  <xsl:attribute name="space-before">7pt</xsl:attribute>
  <xsl:attribute name="text-align">justify</xsl:attribute>
  <xsl:attribute name="font-size">11pt</xsl:attribute>
  <xsl:attribute name="line-height">16pt</xsl:attribute>
  <xsl:attribute name="font-family">
   <xsl:attribute name="font-family">
    <xsl:value-of select="$textfont"/>
  </xsl:attribute></xsl:attribute>
</xsl:attribute-set>
  
  
  <xsl:attribute-set name="paragraph-right">
    <xsl:attribute name="space-before">7pt</xsl:attribute>
    <xsl:attribute name="text-align">right</xsl:attribute>
    <xsl:attribute name="font-size">11pt</xsl:attribute>
    <xsl:attribute name="line-height">16pt</xsl:attribute>
    <xsl:attribute name="font-family">
      <xsl:attribute name="font-family">
        <xsl:value-of select="$textfont"/>
      </xsl:attribute></xsl:attribute>
  </xsl:attribute-set>

<xsl:attribute-set name="paragraph-tight" use-attribute-sets="paragraph">
  <xsl:attribute name="space-before">0pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="contrib-block" use-attribute-sets="sans-serif">
  <xsl:attribute name="font-size">8pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="contrib"/>

<xsl:attribute-set name="aff" use-attribute-sets="contrib"/>

<xsl:attribute-set name="address">
  <xsl:attribute name="keep-together.within-page">always</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="address-line"/>

<xsl:attribute-set name="media-object"/>

<xsl:attribute-set name="email" use-attribute-sets="monospace">
  <xsl:attribute name="font-weight">normal</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="link" use-attribute-sets="sans-serif">
  <xsl:attribute name="font-weight">normal</xsl:attribute>
  <xsl:attribute name="color">midnightblue</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="ext-link"/>

<xsl:attribute-set name="uri"/>

<xsl:attribute-set name="xref"/>

<xsl:attribute-set name="copyright-line"/>

<xsl:attribute-set name="funding-source"/>

<xsl:attribute-set name="inline-formula"/>

<xsl:attribute-set name="object-id" use-attribute-sets="sans-serif">
  <xsl:attribute name="font-size">75%</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="array"/>

<xsl:attribute-set name="author-notes" use-attribute-sets="panel"/>

<xsl:attribute-set name="disp-formula-group"/>

<xsl:attribute-set name="disp-quote" use-attribute-sets="panel">
  <xsl:attribute name="margin-left">2pc</xsl:attribute>
  <xsl:attribute name="text-align">justify</xsl:attribute>
  <xsl:attribute name="margin-right">2pc</xsl:attribute>
  <xsl:attribute name="font-size">9pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="fn-group" use-attribute-sets="section"/>

<xsl:attribute-set name="license"/>

<xsl:attribute-set name="long-desc"/>

<xsl:attribute-set name="open-access"/>

<xsl:attribute-set name="sig-block"/>

<xsl:attribute-set name="attrib"/>

<xsl:attribute-set name="boxed-text" use-attribute-sets="box"/>

<xsl:attribute-set name="chem-struct-box" use-attribute-sets="panel"/>

<xsl:attribute-set name="chem-struct" use-attribute-sets="panel"/>

<xsl:attribute-set name="chem-struct-inline"/>

<xsl:attribute-set name="fig-box" use-attribute-sets="box"/>

<xsl:attribute-set name="fig" use-attribute-sets="panel"/>

<xsl:attribute-set name="list" use-attribute-sets="panel"/>

<xsl:attribute-set name="sub-list"/>

<xsl:attribute-set name="def-list" use-attribute-sets="panel"/>

<xsl:attribute-set name="sub-def-list"/>

<xsl:attribute-set name="list-item" use-attribute-sets="paragraph"/>

<xsl:attribute-set name="def-item"/>

<xsl:attribute-set name="def-list-head"/>

<xsl:attribute-set name="term-head" use-attribute-sets="label">
  <xsl:attribute name="width">
    <xsl:value-of select="$mainindent"/>
  </xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="def-head" use-attribute-sets="label"/>

<xsl:attribute-set name="def-list-term">
  <xsl:attribute name="font-weight">bold</xsl:attribute>
  <xsl:attribute name="keep-with-next.within-page">always</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="def-list-def">
  <xsl:attribute name="margin-left">
    <xsl:value-of select="$mainindent"/>
  </xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="list-item-label">
  <xsl:attribute name="text-align">left</xsl:attribute>
  <xsl:attribute name="font-weight">bold</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="preformat-box" use-attribute-sets="panel"/>

<xsl:attribute-set name="preformat">
  <xsl:attribute name="white-space-treatment">preserve</xsl:attribute>
  <xsl:attribute name="white-space-collapse">false</xsl:attribute>
  <xsl:attribute name="linefeed-treatment">preserve</xsl:attribute>
  <xsl:attribute name="font-family">Georgia</xsl:attribute>
  <xsl:attribute name="font-size">11pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="speech"/>

<xsl:attribute-set name="supplementary" use-attribute-sets="box"/>

<xsl:attribute-set name="table-box" use-attribute-sets="box"/>

<xsl:attribute-set name="table-wrap" use-attribute-sets="panel">
  <xsl:attribute name="font-size">9pt</xsl:attribute>
  <xsl:attribute name="start-indent">0pc</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="caption"/>

<xsl:attribute-set name="textual-form"/>

<xsl:attribute-set name="disp-formula" use-attribute-sets="panel"/>

<xsl:attribute-set name="statement" use-attribute-sets="panel"/>

<xsl:attribute-set name="table-wrap-foot"/>

<xsl:attribute-set name="verse" use-attribute-sets="panel">
  <xsl:attribute name="space-before">4pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="verse-line">
  <xsl:attribute name="start-indent">2pc</xsl:attribute>
  <xsl:attribute name="text-indent">-2pc</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="ref-list-section" use-attribute-sets="section"/>

<xsl:attribute-set name="ref-list-block" use-attribute-sets="panel">
  <xsl:attribute name="provisional-distance-between-starts">0pc</xsl:attribute>
  <xsl:attribute name="provisional-label-separation">6pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="ref-list-item" use-attribute-sets="paragraph"/>

<xsl:attribute-set name="ref"/>

<xsl:attribute-set name="citation" use-attribute-sets="paragraph">
  <xsl:attribute name="start-indent">1pc</xsl:attribute>
  <xsl:attribute name="text-indent">-1pc</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="endnote"/>

<xsl:attribute-set name="footnote-body" use-attribute-sets="outset">
  <xsl:attribute name="space-before">4pt</xsl:attribute>
  <xsl:attribute name="font-family">
    <xsl:value-of select="$textfont"/>
  </xsl:attribute>
  <xsl:attribute name="font-size">9pt</xsl:attribute>
  <xsl:attribute name="font-weight">normal</xsl:attribute>
  <xsl:attribute name="line-height">10pt</xsl:attribute>
</xsl:attribute-set>

<xsl:attribute-set name="footnote-ref" use-attribute-sets="superscript"/>

<xsl:attribute-set name="float">
  <xsl:attribute name="float">before</xsl:attribute>
  <xsl:attribute name="margin-bottom">4pt</xsl:attribute>
</xsl:attribute-set>


<!-- ============================================================= -->
<!-- TOP-LEVEL TEMPLATES                                           -->
<!-- ============================================================= -->


<xsl:template match="/">
  <fo:root>
    <fo:layout-master-set>
      <xsl:call-template name="define-simple-page-masters"/>
      <xsl:call-template name="define-page-sequences"/>
    </fo:layout-master-set>
      <xsl:call-template name="set-fop-metadata"/>
    <xsl:apply-templates/>
  </fo:root>
</xsl:template>


<xsl:template match="article">
  <fo:page-sequence master-reference="cover-sequence" force-page-count="odd">
    <xsl:call-template name="define-footnote-separator"/>
    <fo:flow flow-name="body">
      <fo:block line-stacking-strategy="font-height"
        line-height-shift-adjustment="disregard-shifts">
        <xsl:call-template name="set-article-cover-page"/>
      </fo:block>
    </fo:flow>
  </fo:page-sequence>

  <!-- Populate the content sequence -->
  <fo:page-sequence master-reference="content-sequence"
    initial-page-number="1">
    
    <fo:static-content flow-name="recto-header">
      <fo:block xsl:use-attribute-sets="page-header">
        <xsl:call-template name="make-page-header">
          <xsl:with-param name="face" select="'recto'"/>
        </xsl:call-template>
      </fo:block>
    </fo:static-content>
    <fo:static-content flow-name="verso-header">
      <fo:block xsl:use-attribute-sets="page-header">
        <xsl:call-template name="make-page-header">
          <xsl:with-param name="face" select="'verso'"/>
        </xsl:call-template>
      </fo:block>
    </fo:static-content>
    <xsl:call-template name="define-footnote-separator"/>
    <fo:flow flow-name="body">
      <fo:block line-stacking-strategy="font-height"
        line-height-shift-adjustment="disregard-shifts"
         widows="2" orphans="2">

        <!-- set the article opener, body, and backmatter -->
        <xsl:call-template name="set-article-opener"/>
       
        <xsl:call-template name="set-article"/>
        
      </fo:block>
      
    </fo:flow>
  </fo:page-sequence>

  <!-- produce document diagnostics after the end of 
       the article; this has a page sequence in it
       and all else needed -->
    <xsl:call-template name="run-diagnostics"/>
</xsl:template>

<xsl:template name="define-footnote-separator">
  <fo:static-content flow-name="xsl-footnote-separator">
    <fo:block end-indent="4in" margin-top="12pt" space-after="8pt"
      border-width="0.5pt" border-bottom-style="solid"/>
  </fo:static-content>
</xsl:template>

<xsl:template name="define-page-sequences">

  <!-- cover-sequence master is 'blank' for blank pages
      and 'cover' otherwise -->
  <fo:page-sequence-master master-name="cover-sequence">
    <fo:repeatable-page-master-alternatives>
      <fo:conditional-page-master-reference master-reference="cover"/>
      <fo:conditional-page-master-reference master-reference="blank"
        blank-or-not-blank="blank"/>
    </fo:repeatable-page-master-alternatives>
  </fo:page-sequence-master>

  <!-- content-sequence master is:  
     first, (verso, recto)+ -->
  <fo:page-sequence-master master-name="content-sequence">
    <fo:single-page-master-reference master-reference="first"/>
    <fo:repeatable-page-master-alternatives>
      <fo:conditional-page-master-reference odd-or-even="even"
        master-reference="verso"/>
      <fo:conditional-page-master-reference odd-or-even="odd"
        master-reference="recto"/>
    </fo:repeatable-page-master-alternatives>
  </fo:page-sequence-master>

  <!-- diagnostics-sequence master is: 
       (recto, verso)+ -->
  <fo:page-sequence-master master-name="diagnostics-sequence">
    <fo:repeatable-page-master-alternatives>
      <fo:conditional-page-master-reference odd-or-even="odd"
        master-reference="recto"/>
      <fo:conditional-page-master-reference odd-or-even="even"
        master-reference="verso"/>
    </fo:repeatable-page-master-alternatives>
  </fo:page-sequence-master>
</xsl:template>

<xsl:template name="define-simple-page-masters">
  <!-- blank and cover are similar -->
  <!-- cover page uses recto margins -->
  <fo:simple-page-master master-name="cover" page-height="11in"
    page-width="8.5in" margin-top="0.5in" margin-bottom="1.0in"
    margin-left="1.25in" margin-right="1.25in">
    <fo:region-body region-name="body" margin-top="24pt" margin-bottom="0in"
      margin-left="0in" margin-right="0in"/>
  </fo:simple-page-master>

  <!-- blank page -->
  <fo:simple-page-master master-name="blank" page-height="11in"
    page-width="8.5in" margin-top="0.5in" margin-bottom="1.0in"
    margin-left="1.25in" margin-right="1.25in">
    <fo:region-body region-name="body" margin-top="24pt" margin-bottom="0in"
      margin-left="0in" margin-right="0in"/>
  </fo:simple-page-master>

  <!-- first has recto margins -->
  <fo:simple-page-master master-name="first" page-height="11in"
    page-width="8.5in" margin-top="0.5in" margin-bottom="1in"
    margin-left="1.25in" margin-right="1.25in">
    <fo:region-body region-name="body" margin-top="24pt" margin-bottom="0in"
      margin-left="0in" margin-right="0in"/>
  </fo:simple-page-master>

  <!-- verso page -->
  <fo:simple-page-master master-name="verso" page-height="11in"
    page-width="8.5in" margin-top="0.5in" margin-bottom="1.0in"
    margin-left="1.25in" margin-right="1.25in">
    <fo:region-body region-name="body" margin-top="36pt" margin-bottom="0in"
      margin-left="0in" margin-right="0in"/>
    <fo:region-before region-name="verso-header" display-align="before"
      extent="36pt"/>
  </fo:simple-page-master>

  <!-- recto page -->
  <fo:simple-page-master master-name="recto" page-height="11in"
    page-width="8.5in" margin-top="0.5in" margin-bottom="1.0in"
    margin-left="1.25in" margin-right="1.25in">
    <fo:region-body region-name="body" margin-top="36pt" margin-bottom="0in"
      margin-left="0in" margin-right="0in"/>
    <fo:region-before region-name="recto-header" extent="36pt"
      display-align="before"/>
  </fo:simple-page-master>
</xsl:template>


<xsl:template name="make-page-header">
  <!-- Pass $face in as 'recto' or 'verso' to get titles and page nos
       on facing pages -->
  <xsl:param name="face"/>
  <xsl:param name="center-cell">
    <fo:block/>
  </xsl:param>

    <fo:table border-style="none" width="100%">
      <fo:table-body>
        <fo:table-row>
          <xsl:choose>
            <xsl:when test="$face='recto'">
              <fo:table-cell xsl:use-attribute-sets="page-header-title-cell">
                <fo:block text-align="left">
                  <xsl:call-template name="page-header-title"/>
                </fo:block>
              </fo:table-cell>
            </xsl:when>
            <xsl:when test="$face='verso'">
              <fo:table-cell xsl:use-attribute-sets="page-header-pageno-cell">
                <fo:block text-align="left">
                  <fo:page-number/>
                </fo:block>
              </fo:table-cell>
            </xsl:when>
            <xsl:otherwise/>
          </xsl:choose>
          <fo:table-cell>
            <xsl:copy-of select="$center-cell"/>
          </fo:table-cell>
          <xsl:choose>
            <xsl:when test="$face='verso'">
              <fo:table-cell xsl:use-attribute-sets="page-header-title-cell">
                <fo:block text-align="right">
                  <xsl:call-template name="page-header-title"/>
                </fo:block>
              </fo:table-cell>
            </xsl:when>
            <xsl:when test="$face='recto'">
              <fo:table-cell xsl:use-attribute-sets="page-header-pageno-cell">
                <fo:block text-align="right">
                  <fo:page-number/>
                </fo:block>
              </fo:table-cell>

            </xsl:when>
            <xsl:otherwise/>
          </xsl:choose>
        </fo:table-row>
      </fo:table-body>
    </fo:table>
</xsl:template>


<xsl:template name="set-fop-metadata">
<fo:declarations>
  <x:xmpmeta xmlns:x="adobe:ns:meta/">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
      <rdf:Description rdf:about=""
          xmlns:dc="http://purl.org/dc/elements/1.1/">
        <!-- Dublin Core properties go here -->
	<xsl:for-each select="/article/front/article-meta">
		<xsl:for-each select="contrib-group">
			<dc:creator>
				<xsl:for-each select="contrib">      
				    	<xsl:apply-templates select="anonymous | collab | name" mode="fop-metadata"/>
				</xsl:for-each>
			</dc:creator>
		</xsl:for-each>
        	<xsl:apply-templates mode="fop-metadata" select="article-id"/>
	</xsl:for-each>
	<xsl:for-each select="/article/front/article-meta/title-group">
        	<xsl:apply-templates mode="fop-metadata" select="article-title"/>
        	<xsl:apply-templates mode="fop-metadata" select="abstract"/>
	</xsl:for-each>


      </rdf:Description>
      <rdf:Description rdf:about=""
          xmlns:xmp="http://ns.adobe.com/xap/1.0/">
        <!-- XMP properties go here -->
        <xmp:CreatorTool>meXml: Martin Paul Eve's XML Generator. https://www.martineve.com/</xmp:CreatorTool>
      </rdf:Description>
    </rdf:RDF>
  </x:xmpmeta>
</fo:declarations>
</xsl:template>


<xsl:template match="anonymous" mode="fop-metadata">
    <xsl:text>Anonymous</xsl:text>
</xsl:template>


<xsl:template match="collab" mode="fop-metadata">
      <xsl:apply-templates mode="fop-metadata"/>
</xsl:template>



<xsl:template match="contrib/name" mode="fop-metadata">
    <!-- (surname, given-names?, prefix?, suffix?) -->
    <xsl:call-template name="write-name"/>
</xsl:template>

<xsl:template match="article-title" mode="fop-metadata">
	<dc:title><xsl:value-of select="."/></dc:title>
</xsl:template>

<xsl:template match="article-id" mode="fop-metadata">
	<dc:identifier><xsl:value-of select="."/></dc:identifier>
</xsl:template>

<xsl:template match="article-id" mode="plain">
	<xsl:value-of select="."/>
</xsl:template>

<xsl:template match="abstract" mode="fop-metadata">
	<dc:description><xsl:value-of select="."/></dc:description>
</xsl:template>

<xsl:template name="set-article-cover-page">

  <!-- the journal title on a blue bar background -->
  <fo:block-container>
  <xsl:for-each select="/article/front/journal-meta">
		<fo:block-container display-align="center" width="100%">
		  <fo:block background-color="#000000" width="100%" text-align="left" font-size="0"
		    line-height="0" margin-top="100px">
			  <xsl:element name="fo:external-graphic">
			    <xsl:attribute name="src"><xsl:value-of select="$logo"></xsl:value-of></xsl:attribute>
			    <xsl:attribute name="content-height">70%</xsl:attribute>
			    <xsl:attribute name="content-width">70%</xsl:attribute>
			    <xsl:attribute name="scaling">uniform</xsl:attribute>
			    <xsl:attribute name="margin-top">50px</xsl:attribute>
			  </xsl:element>
			</fo:block>
		</fo:block-container>
		<fo:block space-after="12.pt">
			<xsl:apply-templates mode="cover-page" select="uri"/>
			<xsl:apply-templates mode="cover-page" select="issn"/>
		</fo:block>
  </xsl:for-each>
  </fo:block-container>

  <!-- article data -->
  <xsl:for-each select="/article/front/article-meta">
  <fo:table space-after="5pt" border-style="none">
    <fo:table-body>
      <fo:table-row width="100%">
        <fo:table-cell width="1.5in"><fo:block><xsl:text>Author(s):</xsl:text></fo:block></fo:table-cell>
	<fo:table-cell>
	<xsl:for-each select="contrib-group/contrib">      
	<fo:block>
		    <xsl:call-template name="contrib-identify-cover"/>
		    <xsl:call-template name="contrib-info-cover"/>
	</fo:block>
	</xsl:for-each>
	</fo:table-cell>
	</fo:table-row>

      <fo:table-row width="100%">
        <fo:table-cell width="1.5in"><fo:block><xsl:text>Affiliation(s):</xsl:text></fo:block></fo:table-cell>
	<fo:table-cell>
	<fo:block>
	<xsl:apply-templates select="aff" mode="contrib"/>
	</fo:block>
	</fo:table-cell>
	</fo:table-row>

	<fo:table-row width="100%">
		<fo:table-cell width="1.5in"><fo:block><xsl:text>Title:</xsl:text></fo:block></fo:table-cell>
		<fo:table-cell>
			<fo:block>
				<xsl:for-each select="/article/front/article-meta/title-group">
					<xsl:apply-templates mode="cover-page" select="article-title"/>
				</xsl:for-each>
			</fo:block>
		</fo:table-cell>
	</fo:table-row>

	<fo:table-row width="100%">
		<fo:table-cell width="1.5in"><fo:block><xsl:text>Date:</xsl:text></fo:block></fo:table-cell>
		<fo:table-cell>
			<fo:block>
				<xsl:for-each select="/article/front/article-meta">
					<xsl:apply-templates mode="metadata" select="pub-date"/>
				</xsl:for-each>
			</fo:block>
		</fo:table-cell>
	</fo:table-row>

	<fo:table-row width="100%">
		<fo:table-cell width="1.5in"><fo:block><xsl:text>Volume:</xsl:text></fo:block></fo:table-cell>
		<fo:table-cell>
			<fo:block>
			       <xsl:apply-templates mode="cover-page" select="volume"/>
			</fo:block>
		</fo:table-cell>
	</fo:table-row>

	<fo:table-row width="100%">
		<fo:table-cell width="1.5in"><fo:block><xsl:text>Issue:</xsl:text></fo:block></fo:table-cell>
		<fo:table-cell>
			<fo:block>
			       <xsl:apply-templates mode="cover-page" select="issue"/>
			</fo:block>
		</fo:table-cell>
	</fo:table-row>

	<fo:table-row width="100%">
		<fo:table-cell width="1.5in"><fo:block><xsl:text>URL:</xsl:text></fo:block></fo:table-cell>
		<fo:table-cell>
			<fo:block>
			  <xsl:variable name="contents" select="self-uri"/>
			  <fo:basic-link external-destination="url('{$contents}')" xsl:use-attribute-sets="link">
			    <xsl:value-of select="$contents"/>
			  </fo:basic-link>
			</fo:block>
		</fo:table-cell>
	</fo:table-row>


	<xsl:for-each select="/article/front/article-meta/article-id">
	<fo:table-row width="100%">
		<fo:table-cell width="1.5in"><fo:block><xsl:choose>
        <xsl:when test="@pub-id-type='art-access-id'">Accession ID</xsl:when>
        <xsl:when test="@pub-id-type='coden'">Coden</xsl:when>
        <xsl:when test="@pub-id-type='doi'">DOI</xsl:when>
        <xsl:when test="@pub-id-type='manuscript'">Manuscript ID</xsl:when>
        <xsl:when test="@pub-id-type='medline'">Medline ID</xsl:when>
        <xsl:when test="@pub-id-type='pii'">Publisher Item ID</xsl:when>
        <xsl:when test="@pub-id-type='pmid'">PubMed ID</xsl:when>
        <xsl:when test="@pub-id-type='publisher-id'">Publisher ID</xsl:when>
        <xsl:when test="@pub-id-type='sici'">Serial Item and Contribution
          ID</xsl:when>
        <xsl:when test="@pub-id-type='doaj'">DOAJ ID</xsl:when>
        <xsl:otherwise>
          <xsl:text>Article Id</xsl:text>
          <xsl:for-each select="@pub-id-type">
            <xsl:text> (</xsl:text>
            <fo:inline xsl:use-attribute-sets="data">
              <xsl:value-of select="."/>
            </fo:inline>
            <xsl:text>)</xsl:text>
          </xsl:for-each>
        </xsl:otherwise>
      </xsl:choose>:</fo:block></fo:table-cell>
		<fo:table-cell>
			<fo:block>
			  <xsl:choose>
			    <xsl:when test="@pub-id-type='doi'">
			      <xsl:variable name="contents" select="."/>
			      <fo:basic-link external-destination="url('http://dx.doi.org/{$contents}')" xsl:use-attribute-sets="link">
			        http://dx.doi.org/<xsl:value-of select="$contents"/>
			      </fo:basic-link>
			    </xsl:when>
			    <xsl:otherwise>
			      <xsl:apply-templates mode="cover-page" select="."/>
			    </xsl:otherwise>
			  </xsl:choose>
			       
			</fo:block>
		</fo:table-cell>
	</fo:table-row>
	</xsl:for-each>
	</fo:table-body>
	</fo:table>


    <xsl:variable name="abstracts"
          select="/article/front/article-meta/abstract[not(@abstract-type='toc')] |
          /article/front/article-meta/trans-abstract[not(@abstract-type='toc')]"/>

    <xsl:if test="$abstracts">
      <xsl:call-template name="banner-rule"/>
    </xsl:if>

    <fo:block space-after="10px"><xsl:text>Abstract:</xsl:text></fo:block>

    <xsl:apply-templates mode="cover-page" select="$abstracts"/>

    <xsl:call-template name="banner-rule"/>

  </xsl:for-each>

</xsl:template>

<xsl:template name="make-journal-metadata-table">
  <!-- Builds a table listing journal-level metadata
       Don't be confused: this entire table fits into a table
       cell on the cover page -->
  <xsl:for-each select="/article/front/journal-meta">
    <!-- start the table -->
    <fo:table border-style="solid" border-width="1pt" width="2.75in">
      <fo:table-body>
        <xsl:call-template name="make-metadata-cell">
          <xsl:with-param name="contents">
            <fo:wrapper xsl:use-attribute-sets="coverpage-heading">
              <xsl:text>Journal Information</xsl:text>
            </fo:wrapper>
          </xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates mode="metadata"/>
      </fo:table-body>
    </fo:table>
  </xsl:for-each>
</xsl:template>


<xsl:template name="set-article">
  
  <xsl:apply-templates select="/article/body"/>
  
  <xsl:apply-templates select="/article/back"/>

  <xsl:apply-templates select="/article/floats-group"/>

</xsl:template>

<xsl:template name="set-article-opener">
  <xsl:for-each select="/article/front/article-meta">

    <fo:block>
      <xsl:call-template name="set-copyright-note"/>
      <xsl:apply-templates select="title-group/*[not(self::abstract)]"/>
    </fo:block>

    <xsl:call-template name="banner-rule"/>

    <fo:block xsl:use-attribute-sets="contrib-block">
      <xsl:apply-templates select="contrib-group" mode="opener"/>
      <xsl:apply-templates select="aff" mode="opener"/>
      <xsl:apply-templates select="author-notes" mode="opener"/>
    </fo:block>

    <xsl:call-template name="banner-rule"/>

  </xsl:for-each>
</xsl:template>


<xsl:template name="banner-rule">
  <fo:block space-before="8pt" space-after="8pt"
    border-bottom-style="solid" border-bottom-width="0.5pt"/>
</xsl:template>


<xsl:template name="page-header-title">
  <xsl:for-each select="/article/front/article-meta/title-group/alt-title
                        [@alt-title-type='running-head']">
    <xsl:apply-templates mode="page-header-text"/>
  </xsl:for-each>
  <xsl:if test="not(/article/front/article-meta/title-group/alt-title
                        [@alt-title-type='running-head'])">
    <xsl:for-each
      select="/article/front/article-meta/title-group/article-title">
    <xsl:apply-templates mode="page-header-text"/>
  </xsl:for-each>
  </xsl:if>
</xsl:template>


<xsl:template match="break" mode="page-header-text">
  <!-- in page headers, line breaks are rendered as plain spaces -->
  <xsl:text> </xsl:text>
</xsl:template>


<xsl:template match="*" mode="page-header-text">
  <!-- inline elements are handled as usual, except their contents
       are processed in mode page-header-text -->
  <xsl:apply-templates select="." mode="format">
    <xsl:with-param name="contents">
      <xsl:apply-templates mode="cover-page"/>
    </xsl:with-param>
  </xsl:apply-templates>
</xsl:template>


<xsl:template match="fn | xref" mode="page-header-text"/>
<!-- footnotes and cross-references are not processed in page-header-text
     mode (used for displaying titles and subtitles on the cover
     page) -->


<!-- ============================================================= -->
<!-- METADATA PROCESSING                                           -->
<!-- ============================================================= -->

<!-- For the cover page -->


<xsl:template match="journal-id" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Journal ID</xsl:text>
      <xsl:for-each select="@journal-id-type">
        <xsl:text> (</xsl:text>
        <fo:inline xsl:use-attribute-sets="data">
          <xsl:value-of select="."/>
        </fo:inline>
        <xsl:text>)</xsl:text>
      </xsl:for-each>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<xsl:template match="journal-id" mode="cover-page">
	<fo:block xsl:use-attribute-sets="journal-title" margin-left="10px">
          <xsl:apply-templates />
        </fo:block>
</xsl:template>

<xsl:template match="uri" mode="cover-page">
	<fo:block xsl:use-attribute-sets="journal-metadata" text-align="right">
          <xsl:call-template name="make-external-link-no-attribute-set" />
        </fo:block>
</xsl:template>

<xsl:template match="self-uri" mode="cover-page">
          <xsl:call-template name="make-external-link-no-attribute-set" />
</xsl:template>

<xsl:template match="issn" mode="cover-page">
  <xsl:call-template name="colon-separated-entry">
    <xsl:with-param name="label">
      <xsl:text>ISSN</xsl:text>
      <xsl:call-template name="append-pub-type"/>
    </xsl:with-param>
  </xsl:call-template>

</xsl:template>


<xsl:template match="journal-title-group" mode="metadata">
  <xsl:apply-templates mode="metadata"/>
</xsl:template>


<!-- journal-title-group content:
     (journal-title*, journal-subtitle*, trans-title-group*,
     abbrev-journal-title*) -->

<xsl:template match="journal-title" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Title</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="journal-subtitle" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Subtitle</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="trans-title-group" mode="metadata">
  <xsl:apply-templates mode="metadata"/>
</xsl:template>


<!-- trans-title-group content: (trans-title, trans-subtitle*) -->

<xsl:template match="trans-title" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Translated Title</xsl:text>
      <xsl:for-each select="@xml:lang">
        <xsl:text> (</xsl:text>
        <fo:inline xsl:use-attribute-sets="data">
          <xsl:value-of select="."/>
        </fo:inline>
        <xsl:text>)</xsl:text>
      </xsl:for-each>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="trans-subtitle" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Translated Subtitle</xsl:text>
      <xsl:for-each select="@xml:lang">
        <xsl:text> (</xsl:text>
        <fo:inline xsl:use-attribute-sets="data">
          <xsl:value-of select="."/>
        </fo:inline>
        <xsl:text>)</xsl:text>
      </xsl:for-each>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<xsl:template match="abbrev-journal-title" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Abbreviated Title</xsl:with-param>
  </xsl:call-template>
</xsl:template>

<xsl:template match="issn" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>ISSN</xsl:text>
      <xsl:call-template name="append-pub-type"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="isbn" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>ISBN</xsl:text>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="publisher" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Publisher</xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:apply-templates select="publisher-name" mode="metadata-inline"/>
      <xsl:apply-templates select="publisher-loc" mode="metadata-inline"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="publisher-name" mode="metadata-inline">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="publisher-loc" mode="metadata-inline">
  <fo:inline xsl:use-attribute-sets="generated"> (</fo:inline>
  <xsl:apply-templates/>
  <fo:inline xsl:use-attribute-sets="generated">)</fo:inline>
</xsl:template>


<xsl:template match="notes" mode="metadata">
  <xsl:call-template name="metadata-area-cell">
    <xsl:with-param name="label">Notes</xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:call-template name="set-outset-label"/>
      <xsl:apply-templates/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="email" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Email</xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:apply-templates select="."/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="ext-link" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>External link</xsl:text>
      <xsl:for-each select="ext-link-type">
        <xsl:text> (</xsl:text>
        <fo:inline xsl:use-attribute-sets="data">
          <xsl:value-of select="."/>
        </fo:inline>
        <xsl:text>)</xsl:text>
      </xsl:for-each>
    </xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:apply-templates select="."/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="uri" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">URI</xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:apply-templates select="."/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="product" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Product Information</xsl:text>
    </xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:choose>
        <xsl:when test="normalize-space(@xlink:href)">
          <xsl:call-template name="make-external-link"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="history/date" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Date</xsl:text>
      <xsl:for-each select="@date-type">
        <xsl:choose>
          <xsl:when test=".='accepted'"> accepted</xsl:when>
          <xsl:when test=".='received'"> received</xsl:when>
          <xsl:when test=".='rev-request'"> revision requested</xsl:when>
          <xsl:when test=".='rev-recd'"> revision received</xsl:when>
        </xsl:choose>
      </xsl:for-each>
    </xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:call-template name="format-date"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>



<xsl:template match="self-uri" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Self URI</xsl:text>
    </xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:choose>
        <xsl:when test="normalize-space()">
          <xsl:apply-templates/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="@xlink:href"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<xsl:template match="pub-date" mode="metadata">
	<fo:inline xsl:use-attribute-sets="coverpage-default">
		<xsl:call-template name="format-date"/>
	</fo:inline>
</xsl:template>

<!--<xsl:template match="pub-date" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Publication date</xsl:text>
      <xsl:call-template name="append-pub-type"/>
    </xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:call-template name="format-date"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>-->


<xsl:template match="volume | issue" mode="metadata-inline">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="volume-id | issue-id" mode="metadata-inline">
  <fo:inline xsl:use-attribute-sets="generated">
    <xsl:text> (</xsl:text>
    <xsl:for-each select="@pub-id-type">
      <fo:inline xsl:use-attribute-sets="data">
        <xsl:value-of select="."/>
      </fo:inline>
      <xsl:text> </xsl:text>
    </xsl:for-each>
    <xsl:text>ID: </xsl:text>
  </fo:inline>
  <xsl:apply-templates/>
  <fo:inline xsl:use-attribute-sets="generated">)</fo:inline>
</xsl:template>


<xsl:template match="volume-series" mode="metadata-inline">
  <xsl:if test="preceding-sibling::volume">
    <fo:inline xsl:use-attribute-sets="generated">,</fo:inline>
  </xsl:if>
  <xsl:text> </xsl:text>
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="volume" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Volume</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="volume-id" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Volume ID</xsl:text>
      <xsl:for-each select="@pub-id-type">
        <xsl:text> (</xsl:text>
        <fo:inline xsl:use-attribute-sets="data">
          <xsl:value-of select="."/>
        </fo:inline>
        <xsl:text>)</xsl:text>
      </xsl:for-each>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="volume-series" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Series</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="issue-title" mode="metadata-inline">
  <fo:inline xsl:use-attribute-sets="generated">
    <xsl:if test="preceding-sibling::issue">,</xsl:if>
  </fo:inline>
  <xsl:text> </xsl:text>
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="issue" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Issue</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="issue-id" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Issue ID</xsl:text>
      <xsl:for-each select="@pub-id-type">
        <xsl:text> (</xsl:text>
        <fo:inline xsl:use-attribute-sets="data">
          <xsl:value-of select="."/>
        </fo:inline>
        <xsl:text>)</xsl:text>
      </xsl:for-each>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="issue-title" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Issue title</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="issue-sponsor" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Issue sponsor</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="issue-part" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Issue part</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="elocation-id" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Electronic Location
      Identifier</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<!-- isbn is already matched in mode 'metadata' above -->


<xsl:template match="supplement" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Supplement Info</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="related-article | related-object" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:text>Related </xsl:text>
      <xsl:choose>
        <xsl:when test="self::related-object">object</xsl:when>
        <xsl:otherwise>article</xsl:otherwise>
      </xsl:choose>
      <xsl:for-each select="@related-article-type | @object-type">
        <xsl:text> (</xsl:text>
        <fo:inline xsl:use-attribute-sets="data">
          <xsl:value-of select="translate(.,'-',' ')"/>
        </fo:inline>
        <xsl:text>)</xsl:text>
      </xsl:for-each>
    </xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:choose>
        <xsl:when test="normalize-space(@xlink:href)">
          <xsl:call-template name="make-external-link"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:apply-templates/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="conference" mode="metadata">
  <!-- content model:
    (conf-date, 
     (conf-name | conf-acronym)+, 
     conf-num?, conf-loc?, conf-sponsor*, conf-theme?) -->
  <xsl:choose>
    <xsl:when
      test="not(conf-name[2] | conf-acronym[2] | conf-sponsor |
                conf-theme)">
      <!-- if there is no second name or acronym, and no sponsor
           or theme, we make one line only -->
      <xsl:call-template name="metadata-labeled-entry-cell">
        <xsl:with-param name="label">Conference</xsl:with-param>
        <xsl:with-param name="contents">
          <xsl:apply-templates select="conf-acronym | conf-name"
            mode="metadata-inline"/>
          <xsl:apply-templates select="conf-num" mode="metadata-inline"/>
          <xsl:if test="conf-date | conf-loc">
            <fo:inline xsl:use-attribute-sets="generated"> (</fo:inline>
            <xsl:for-each select="conf-date | conf-loc">
              <xsl:if test="position() = 2">, </xsl:if>
              <xsl:apply-templates select="." mode="metadata-inline"/>
            </xsl:for-each>
            <fo:inline xsl:use-attribute-sets="generated">)</fo:inline>
          </xsl:if>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates mode="metadata"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<xsl:template match="conf-date" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Conference date</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="conf-name" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Conference</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="conf-acronym" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Conference</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="conf-num" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Conference number</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="conf-loc" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Conference location</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="conf-sponsor" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Conference sponsor</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="conf-theme" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Conference theme</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="conf-name | conf-acronym" mode="metadata-inline">
  <!-- we only hit this template if there is at most one of each -->
  <xsl:variable name="following"
    select="preceding-sibling::conf-name | preceding-sibling::conf-acronym"/>
  <!-- if we come after the other, we go in parentheses -->
  <xsl:if test="$following">
    <fo:inline xsl:use-attribute-sets="generated"> (</fo:inline>
  </xsl:if>
  <xsl:apply-templates/>
  <xsl:if test="$following">
    <fo:inline xsl:use-attribute-sets="generated">)</fo:inline>
  </xsl:if>
</xsl:template>


<xsl:template match="conf-num" mode="metadata-inline">
  <xsl:text> </xsl:text>
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="conf-date | conf-loc" mode="metadata-inline">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="article-id" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">
      <xsl:choose>
        <xsl:when test="@pub-id-type='art-access-id'">Accession ID</xsl:when>
        <xsl:when test="@pub-id-type='coden'">Coden</xsl:when>
        <xsl:when test="@pub-id-type='doi'">DOI</xsl:when>
        <xsl:when test="@pub-id-type='manuscript'">Manuscript ID</xsl:when>
        <xsl:when test="@pub-id-type='medline'">Medline ID</xsl:when>
        <xsl:when test="@pub-id-type='pii'">Publisher Item ID</xsl:when>
        <xsl:when test="@pub-id-type='pmid'">PubMed ID</xsl:when>
        <xsl:when test="@pub-id-type='publisher-id'">Publisher ID</xsl:when>
        <xsl:when test="@pub-id-type='sici'">Serial Item and Contribution
          ID</xsl:when>
        <xsl:when test="@pub-id-type='doaj'">DOAJ ID</xsl:when>
        <xsl:otherwise>
          <xsl:text>Article Id</xsl:text>
          <xsl:for-each select="@pub-id-type">
            <xsl:text> (</xsl:text>
            <fo:inline xsl:use-attribute-sets="data">
              <xsl:value-of select="."/>
            </fo:inline>
            <xsl:text>)</xsl:text>
          </xsl:for-each>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<xsl:template match="award-group" mode="metadata">
  <!-- includes (funding-source*, award-id*, principal-award-recipient*, principal-investigator*) -->
  <xsl:apply-templates mode="metadata"/>
</xsl:template>


<xsl:template match="funding-source" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Funded by</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="award-id" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Award ID</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="principal-award-recipient" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Award Recipient</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="principal-investigator" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Principal Investigator</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="funding-statement" mode="metadata">
  <xsl:call-template name="metadata-labeled-entry-cell">
    <xsl:with-param name="label">Funding</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="open-access" mode="metadata">
  <xsl:call-template name="metadata-area-cell">
    <xsl:with-param name="label">Open Access</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="article-categories" mode="metadata">
  <xsl:apply-templates mode="metadata"/>
</xsl:template>


<xsl:template match="article-categories/subj-group" mode="metadata">
  <fo:block xsl:use-attribute-sets="coverpage-block">
    <xsl:call-template name="metadata-block">
      <xsl:with-param name="label">Categories</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </fo:block>
</xsl:template>


<xsl:template match="subj-group" mode="metadata">
  <xsl:apply-templates mode="metadata"/>
</xsl:template>


<xsl:template match="subj-group/subj-group" mode="metadata">
  <xsl:call-template name="metadata-block">
    <xsl:with-param name="contents">
      <xsl:apply-templates mode="metadata"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="subj-group/subject" mode="metadata">
  <xsl:call-template name="metadata-labeled-line">
    <xsl:with-param name="label">Subject</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="series-title" mode="metadata">
  <xsl:call-template name="metadata-labeled-line">
    <xsl:with-param name="label">Series title</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="series-text" mode="metadata">
  <xsl:call-template name="metadata-labeled-line">
    <xsl:with-param name="label">Series description</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="kwd-group" mode="metadata">
  <fo:block xsl:use-attribute-sets="coverpage-block">
    <xsl:call-template name="metadata-block">
      <xsl:with-param name="label">
        <xsl:apply-templates select="title|label" mode="metadata-inline"/>
        <xsl:if test="not(title|label)">Keywords</xsl:if>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </fo:block>
</xsl:template>


<xsl:template match="title" mode="metadata">
  <xsl:apply-templates select="."/>
</xsl:template>


<xsl:template match="kwd" mode="metadata">
  <xsl:call-template name="metadata-labeled-line">
    <xsl:with-param name="label">Keyword</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="compound-kwd" mode="metadata">
  <xsl:call-template name="metadata-block">
    <xsl:with-param name="label">Compound keyword</xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:apply-templates mode="metadata"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="compound-kwd-part" mode="metadata">
  <xsl:call-template name="metadata-labeled-line">
    <xsl:with-param name="label">
      <xsl:text>Keyword part</xsl:text>
      <xsl:for-each select="@content-type">
        <xsl:text> (</xsl:text>
        <fo:inline xsl:use-attribute-sets="data">
          <xsl:value-of select="."/>
        </fo:inline>
        <xsl:text>)</xsl:text>
      </xsl:for-each>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="supplementary-material" mode="metadata">
  <fo:block xsl:use-attribute-sets="coverpage-block">
    <xsl:call-template name="metadata-block">
      <xsl:with-param name="label">Supplementary material</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:call-template name="set-outset-label"/>
        <xsl:apply-templates/>
      </xsl:with-param>
    </xsl:call-template>
  </fo:block>
</xsl:template>


<xsl:template match="counts" mode="metadata">
  <!-- fig-count?, table-count?, equation-count?, ref-count?,
       page-count?, word-count? -->
  <fo:block xsl:use-attribute-sets="coverpage-block">
    <xsl:call-template name="metadata-block">
      <xsl:with-param name="label">Counts</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </fo:block>
</xsl:template>


<xsl:template mode="metadata"
  match="fig-count | table-count | equation-count |
         ref-count | page-count | word-count">
  <xsl:call-template name="metadata-labeled-line">
    <xsl:with-param name="label">
      <xsl:apply-templates select="." mode="metadata-label"/>
    </xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:value-of select="@count"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="fig-count" mode="metadata-label">Figures</xsl:template>


<xsl:template match="table-count" mode="metadata-label">Tables</xsl:template>


<xsl:template match="equation-count" mode="metadata-label"
  >Equations</xsl:template>


<xsl:template match="ref-count" mode="metadata-label"
  >References</xsl:template>


<xsl:template match="page-count" mode="metadata-label">Pages</xsl:template>


<xsl:template match="word-count" mode="metadata-label">Words</xsl:template>


<xsl:template mode="metadata" match="custom-meta-group">
  <fo:block xsl:use-attribute-sets="coverpage-block">
    <xsl:call-template name="metadata-block">
      <xsl:with-param name="label">Custom metadata</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </fo:block>
</xsl:template>


<xsl:template match="custom-meta" mode="metadata">
  <xsl:call-template name="metadata-labeled-line">
    <xsl:with-param name="label">
      <fo:inline xsl:use-attribute-sets="data">
        <xsl:apply-templates select="meta-name" mode="metadata-inline"/>
      </fo:inline>
    </xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:apply-templates select="meta-value" mode="metadata-inline"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template mode="metadata-inline"
  match="meta-name | meta-value | title | label">
  <xsl:apply-templates/>
</xsl:template>


<!-- ============================================================= -->
<!-- Named templates for metadata processing                       -->
<!-- ============================================================= -->
<!-- These generally group related elements into a single metadata
     structure -->

<xsl:template name="volume-info">
  <!-- handles volume?, volume-id*, volume-series? -->
  <xsl:if test="volume | volume-id | volume-series">
    <xsl:choose>
      <xsl:when test="not(volume-id[2]) or not(volume)">
        <!-- if there are no multiple volume-id, or no volume,
             we make one line only -->
        <xsl:call-template name="metadata-labeled-entry-cell">
          <xsl:with-param name="label">Volume</xsl:with-param>
          <xsl:with-param name="contents">
            <xsl:apply-templates select="volume | volume-series"
              mode="metadata-inline"/>
            <xsl:apply-templates select="volume-id" mode="metadata-inline"/>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="volume | volume-id | volume-series"
          mode="metadata"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:if>
</xsl:template>


<xsl:template name="page-info">
  <!-- handles (fpage, lpage?, page-range?) -->
  <xsl:if test="fpage | lpage | page-range">
    <xsl:call-template name="metadata-labeled-entry-cell">
      <xsl:with-param name="label">
        <xsl:text>Page</xsl:text>
        <xsl:if
          test="normalize-space(lpage[not(.=../fpage)])
                 or normalize-space(page-range)">
          <!-- we have multiple pages if lpage exists and is not equal fpage,
             or if we have a page-range -->
          <xsl:text>s</xsl:text>
        </xsl:if>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:value-of select="fpage"/>
        <xsl:if test="normalize-space(lpage[not(.=../fpage)])">
          <xsl:text>-</xsl:text>
          <xsl:value-of select="lpage"/>
        </xsl:if>
        <xsl:for-each select="page-range">
          <xsl:text> (pp. </xsl:text>
          <xsl:value-of select="."/>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:if>
</xsl:template>

<xsl:template name="issue-info">
  <!-- handles issue?, issue-id*, issue-title*, issue-sponsor*,
       issue-part?, supplement? -->
  <xsl:variable name="issue-info"
    select="issue | issue-id | issue-title |
    issue-sponsor | issue-part"/>
  <xsl:choose>
    <xsl:when
      test="$issue-info and not(issue-id[2] | issue-title[2] |
                                issue-sponsor | issue-part)">
      <!-- if there are only one issue, issue-id and issue-title
           and nothing else, we make one line only -->
      <xsl:call-template name="metadata-labeled-entry-cell">
        <xsl:with-param name="label">Issue</xsl:with-param>
        <xsl:with-param name="contents">
          <xsl:apply-templates select="issue | issue-title"
            mode="metadata-inline"/>
          <xsl:apply-templates select="issue-id" mode="metadata-inline"/>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates select="$issue-info" mode="metadata"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!-- ============================================================= -->
<!-- SPECIALIZED FRONT PAGE TEMPLATES                              -->
<!-- ============================================================= -->


<xsl:template name="set-copyright-note">
  <!-- This note is set as a first-page footnote, 
       and has no number or other device.
       The context node is /article/front/article-meta -->
  <xsl:call-template name="make-footnote">
    <xsl:with-param name="contents">
      <xsl:element name="fo:block">
        <xsl:attribute name="line-height">12pt</xsl:attribute>
        <xsl:attribute name="margin-top">10px</xsl:attribute>
          <xsl:apply-templates select="permissions"/>
      </xsl:element>
    </xsl:with-param>
  </xsl:call-template>   
</xsl:template>


<xsl:template match="title-group | trans-title-group">
  <!-- title-group: (article-title, subtitle*, trans-title-group*,
                     alt-title*, fn-group?) -->
  <!-- trans-title-group: (trans-title, trans-subtitle*) -->
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="title-group/article-title">
    <fo:block xsl:use-attribute-sets="firstpage-title">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="title-group/subtitle">
    <fo:block xsl:use-attribute-sets="firstpage-subtitle">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="title-group/alt-title">
  <fo:block xsl:use-attribute-sets="firstpage-alt-title">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template priority="2"
  match="title-group/alt-title[@alt-title-type='running-head']">
  <!-- a running head title is suppressed -->
</xsl:template>


<xsl:template match="trans-title-group/trans-title">
  <fo:block xsl:use-attribute-sets="firstpage-trans-title">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="trans-title-group/trans-subtitle">
  <fo:block xsl:use-attribute-sets="firstpage-trans-subtitle">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="contrib-group">
  <!-- content model of contrib-group:
        (contrib+, 
         (address | aff | author-comment | bio | email |
          ext-link | on-behalf-of | role | uri | xref)*) -->
  <!-- each contrib makes a row: name at left, details at right -->
  <fo:table>
    <fo:table-body>
      <xsl:for-each select="contrib">
        <!-- content model of contrib: 
        ((anonymous | collab | name)*, (degrees)*, 
         (address | aff | author-comment | bio | email |
          ext-link | on-behalf-of | role | uri | xref)*) -->
        <fo:table-row>
          <fo:table-cell>
            <xsl:call-template name="contrib-identify">
              <!-- handles
                 (anonymous | collab | name | degrees | xref) -->
            </xsl:call-template>
          </fo:table-cell>
        </fo:table-row>
      </xsl:for-each>
      <!-- end of contrib -->
    </fo:table-body>
  </fo:table>
</xsl:template>

<xsl:template name="contrib-identify-cover">
  <!-- Placed in a left-hand pane  -->
  <fo:block xsl:use-attribute-sets="coverpage">
    <xsl:apply-templates select="anonymous | collab | name"
      mode="contrib"/>
    <!-- degrees | xref will be handled along with the last
         of these children by the contrib-amend template -->
  </fo:block>
</xsl:template>

<xsl:template name="contrib-identify">
  <!-- Placed in a left-hand pane  -->
  <fo:block xsl:use-attribute-sets="coverpage">
    <xsl:apply-templates select="anonymous | collab | name"
      mode="opener"/>
  </fo:block>
</xsl:template>


<xsl:template match="anonymous" mode="opener">
  <fo:block>
    <xsl:text>Anonymous</xsl:text>
    
  </fo:block>
</xsl:template>


<xsl:template match="collab" mode="opener">
  <fo:block>
      <xsl:apply-templates mode="opener"/>
  </fo:block>
</xsl:template>



<xsl:template match="contrib/name" mode="opener">
  <fo:block>
    <!-- (surname, given-names?, prefix?, suffix?) -->
    <xsl:call-template name="write-name"/>
    
  </fo:block>
</xsl:template>


<xsl:template match="anonymous" mode="contrib">
    <xsl:text>Anonymous</xsl:text>
    <xsl:call-template name="contrib-amend">
      <xsl:with-param name="last-contrib"
        select="not(../following-sibling::contrib)"/>
      <!-- passes Boolean false if we are inside the last
               contrib -->
    </xsl:call-template>
</xsl:template>


<xsl:template match="collab" mode="contrib">
    <fo:inline>
      <xsl:apply-templates/>
      <xsl:call-template name="contrib-amend">
        <xsl:with-param name="last-contrib"
          select="not(../following-sibling::contrib)"/>
          <!-- passes Boolean false if we are inside the last
               contrib -->
      </xsl:call-template>
    </fo:inline>
</xsl:template>



<xsl:template match="contrib/name" mode="contrib">
    <fo:inline>
    <!-- (surname, given-names?, prefix?, suffix?) -->
    <xsl:call-template name="write-name"/>
    <xsl:call-template name="contrib-amend">
        <xsl:with-param name="last-contrib"
          select="not(../following-sibling::contrib)"/>
          <!-- passes Boolean false if we are inside the last
               contrib -->
    </xsl:call-template>
    </fo:inline>
</xsl:template>


<xsl:template name="contrib-amend">
  <!-- the context will be a contrib/anonymous, contrib/collab
       or contrib/name; this template adds contrib/degrees and 
       contrib/xref siblings to the last of these available 
       within the contrib -->
  <xsl:param name="last-contrib" select="false()"/>
  <!-- passed as 'true' for the last contrib only -->
  <xsl:if test="not(following-sibling::anonymous |
                    following-sibling::collab |
                    following-sibling::name)">
    <xsl:apply-templates select="../degrees | ../xref" mode="contrib"/>
    <xsl:if test="$last-contrib">
      <xsl:apply-templates select="parent::contrib/following-sibling::xref"/>
    </xsl:if>
  </xsl:if>
</xsl:template>


<xsl:template match="degrees" mode="contrib">
  <xsl:text>, </xsl:text>
  <xsl:apply-templates/>
</xsl:template>

<xsl:template match="degrees" mode="opener">
<!-- suppress -->
</xsl:template>


<xsl:template match="xref" mode="contrib">
    <fo:inline>
  <xsl:apply-templates select="."/>
    </fo:inline>
</xsl:template>

<xsl:template match="xref" mode="opener">
<!-- suppress -->
</xsl:template>


<xsl:template name="contrib-info">
  <!-- Placed in a right-hand pane -->
    <fo:inline>
    <xsl:apply-templates mode="opener"
      select="address | aff | author-comment | email |
              ext-link | on-behalf-of | role | uri"/>
    </fo:inline>
</xsl:template>

<xsl:template name="contrib-info-cover">
  <!-- Placed in a right-hand pane -->
    <fo:inline>
    <xsl:apply-templates mode="contrib"
      select="address | aff | author-comment | email |
              ext-link | on-behalf-of | role | uri"/>
    </fo:inline>
</xsl:template>


<xsl:template mode="contrib"
  match="address[not(addr-line) or not(*[2])]">
  <!-- when we have no addr-line or a single child, we generate
       a single unlabelled line -->
  <fo:block xsl:use-attribute-sets="address-line">
     <xsl:apply-templates mode="inline"/>
  </fo:block>
</xsl:template>


<xsl:template mode="contrib" match="address">
  <!-- when we have an addr-line we generate an unlabelled block -->
  <fo:block xsl:use-attribute-sets="address">
      <xsl:apply-templates/>
  </fo:block>   
</xsl:template>


<xsl:template mode="contrib" priority="2" match="address/*">
  <!-- being sure to override other templates for these
       element types -->
  <fo:block xsl:use-attribute-sets="address-line">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>

<xsl:template mode="opener" match="aff">
<!-- suppress -->
</xsl:template>

<xsl:template mode="contrib" match="aff">
   <fo:block xsl:use-attribute-sets="coverpage">
     <xsl:variable name="label">
       <xsl:apply-templates select="." mode="label-text"/>
     </xsl:variable>
     <xsl:copy-of select="$label"/>
     <xsl:if test="normalize-space($label)">
       <xsl:text> </xsl:text>
     </xsl:if>
     <xsl:apply-templates/>
   </fo:block>
</xsl:template>


<xsl:template match="aff">
   <fo:block xsl:use-attribute-sets="coverpage">
     <xsl:variable name="label">
       <xsl:apply-templates select="." mode="label-text"/>
     </xsl:variable>
     <xsl:copy-of select="$label"/>
     <xsl:if test="normalize-space($label)">
       <xsl:text> </xsl:text>
     </xsl:if>
     <xsl:apply-templates mode="inline"/>
   </fo:block>
</xsl:template>


<xsl:template match="author-comment | bio" mode="contrib">
  <!-- these elements are not supported in this version -->
</xsl:template>


<xsl:template match="on-behalf-of" mode="contrib">
  <fo:block xsl:use-attribute-sets="contrib">
    <fo:inline xsl:use-attribute-sets="generated">On behalf of </fo:inline>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="role" mode="contrib">

    <xsl:apply-templates/>

</xsl:template>


<xsl:template match="email" mode="contrib">
  <fo:block xsl:use-attribute-sets="contrib">
    <xsl:apply-templates select="."/>
  </fo:block>
</xsl:template>


<xsl:template match="ext-link | uri" mode="contrib">
  <fo:block>
    <xsl:apply-templates select="."/>
  </fo:block>
</xsl:template>


<xsl:template name="set-correspondence-note">
  <!-- context node is article-meta -->
  <xsl:if test="contrib-group/contrib[@corresp='yes']">
    <fo:block space-before="0pt" space-after="0pt">
      <xsl:call-template name="make-footnote">
        <xsl:with-param name="contents">
          <xsl:text>Correspondence to: </xsl:text>
          <xsl:for-each select="contrib-group/contrib[@corresp='yes']">
            <xsl:apply-templates select="name | collab"/>
            <xsl:choose>
              <xsl:when test="email">
                <xsl:text>, </xsl:text>
                <fo:inline xsl:use-attribute-sets="email">
                  <xsl:apply-templates select="email"/>
                </fo:inline>
              </xsl:when>
              <xsl:when test="address">
                <xsl:text>, </xsl:text>
                <xsl:apply-templates select="address"/>
              </xsl:when>
            </xsl:choose>
            <xsl:if test="not(position()=last())">; </xsl:if>
          </xsl:for-each>
          <xsl:text>.</xsl:text>
        </xsl:with-param>
      </xsl:call-template>
    </fo:block>
  </xsl:if>
</xsl:template>



<!-- ============================================================= -->
<!-- Mode "cover-page"                                             -->
<!-- ============================================================= -->
<!-- For processing article titles and subtitles on the cover page,
     where footnotes should not be handled                         -->


<xsl:template mode="cover-page"
  match="/article/front/article-meta/title-group/article-title">
  <fo:block xsl:use-attribute-sets="coverpage">
    <xsl:apply-templates mode="cover-page"/>
  </fo:block>
</xsl:template>

<xsl:template mode="cover-page"
  match="/article/front/article-meta/title-group/subtitle">
  <fo:block xsl:use-attribute-sets="coverpage">
    <xsl:apply-templates mode="cover-page"/>
  </fo:block>
</xsl:template>

<xsl:template mode="cover-page"
  match="/article/front/article-meta/*">
  <fo:block xsl:use-attribute-sets="coverpage">
    <xsl:apply-templates mode="cover-page"/>
  </fo:block>
</xsl:template>

<xsl:template mode="cover-page"
  match="/contrib-group/*">
  <fo:block xsl:use-attribute-sets="coverpage">
    <xsl:apply-templates mode="cover-page"/>
  </fo:block>
</xsl:template>

<xsl:template mode="cover-page" match="trans-title-group">
  <fo:block space-before="0pt" space-after="12pt">
    <xsl:apply-templates mode="cover-page"/>
  </fo:block>
</xsl:template>

<xsl:template mode="cover-page" match="abstract">
  <fo:block space-before="0pt" space-after="12pt" xsl:use-attribute-sets="coverpage-abstract">
    <xsl:apply-templates mode="cover-page"/>
  </fo:block>
</xsl:template>



<xsl:template mode="cover-page" match="trans-title">
  <fo:block xsl:use-attribute-sets="section-title">
    <xsl:text>Translated Title </xsl:text>
    <xsl:if test="../@xml:lang">
      <xsl:text>(</xsl:text>
      <xsl:value-of select="../@xml:lang"/>
      <xsl:text>) </xsl:text>
    </xsl:if>
    <xsl:text>: </xsl:text>
    <xsl:apply-templates mode="cover-page"/>
  </fo:block>
</xsl:template>


<xsl:template mode="cover-page" match="trans-subtitle">
  <fo:block xsl:use-attribute-sets="subsection-title">
    <xsl:apply-templates mode="cover-page"/>
  </fo:block>
</xsl:template>


<xsl:template mode="cover-page" priority="2"
  match="alt-title[@alt-title-type='running-head']"/>


<xsl:template mode="cover-page" match="alt-title">
  <fo:block xsl:use-attribute-sets="block-title">
    <xsl:text>Alternate Title: </xsl:text>
    <xsl:apply-templates mode="cover-page"/>
  </fo:block>
</xsl:template>


<xsl:template mode="cover-page" match="*">
  <!-- inline elements are handled as usual, except their contents
       are processed in mode cover-page -->
  <xsl:apply-templates select="." mode="format">
    <xsl:with-param name="contents">
      <xsl:apply-templates mode="cover-page"/>
    </xsl:with-param>
  </xsl:apply-templates>
</xsl:template>


<xsl:template mode="cover-page" match="fn | xref"/>
<!-- footnotes and cross-references are not processed in cover-page
     mode (used for displaying titles and subtitles on the cover
     page) -->


<!-- ============================================================= -->
<!-- DEFAULT TEMPLATES (mostly in no mode)                         -->
<!-- ============================================================= -->


<xsl:template match="body">
  <fo:block xsl:use-attribute-sets="body">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<!-- ============================================================= -->
<!-- Titles                                                        -->
<!-- ============================================================= -->


<xsl:template name="main-title"
  match="body/*/title |
  back/title | back[not(title)]/*/title" priority="2">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:if test="normalize-space($contents)">
    <fo:block xsl:use-attribute-sets="main-title">
      <xsl:copy-of select="$contents"/>
    </fo:block>
  </xsl:if>
</xsl:template>


<xsl:template name="section-title"
  match="abstract/title | notes/title | body/*/*/title |
	       back[title]/*/title | back[not(title)]/*/*/title">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:if test="normalize-space($contents)">
    <fo:block xsl:use-attribute-sets="section-title">
      <xsl:copy-of select="$contents"/>
    </fo:block>
  </xsl:if>
</xsl:template>


<xsl:template name="subsection-title"
  match="abstract/*/title | body/*/*/*/title |
	       back[title]/*/*/title | back[not(title)]/*/*/*/title">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:if test="normalize-space($contents)">
    <fo:block xsl:use-attribute-sets="subsection-title">
      <xsl:copy-of select="$contents"/>
    </fo:block>
  </xsl:if>
</xsl:template>


<xsl:template name="block-title" priority="2"
  match="abstract/*/*/title | author-notes/title |
         list/title | def-list/title | boxed-text/title |
         verse-group/title | glossary/title | kwd-group/title">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:if test="normalize-space($contents)">
    <fo:block xsl:use-attribute-sets="block-title">
      <xsl:copy-of select="$contents"/>
    </fo:block>
  </xsl:if>
</xsl:template>


<xsl:template match="title">
<!-- default template for any other titles found -->
  <xsl:if test="normalize-space()">
    <fo:block xsl:use-attribute-sets="title">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:if>
</xsl:template>


<xsl:template match="subtitle">
  <xsl:if test="normalize-space()">
    <fo:block xsl:use-attribute-sets="subtitle">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:if>
</xsl:template>


<xsl:template match="label">
  <!-- label is suppressed in default traversal; where
       labels are wanted they are provided by matching
       elements in mode 'label' -->
</xsl:template>


<xsl:template match="sec">
  <fo:block xsl:use-attribute-sets="section">
    <xsl:call-template name="set-outset-label"/>
    <xsl:apply-templates select="title"/>
    <xsl:apply-templates select="sec-meta"/>
    <xsl:apply-templates mode="drop-title"/>
  </fo:block>
</xsl:template>


<xsl:template match="*" mode="drop-title">
  <xsl:apply-templates select="."/>
</xsl:template>


<xsl:template match="title | sec-meta | label" mode="drop-title"/>


<xsl:template match="sec-meta">
 <fo:block xsl:use-attribute-sets="section-metadata">
   <!-- content model: (contrib-group*, kwd-group*, permissions?) -->
   <xsl:apply-templates/>
 </fo:block>
</xsl:template>


<xsl:template match="sec-meta/kwd-group">
  <fo:block xsl:use-attribute-sets="paragraph">
    <fo:inline xsl:use-attribute-sets="generated">
      <xsl:text>Keyword</xsl:text>
      <xsl:if test="count(kwd) &gt; 1">s</xsl:if>
      <xsl:text>:</xsl:text>
    </fo:inline>
    <xsl:for-each select="kwd">
    <xsl:text> </xsl:text>
      <xsl:apply-templates/>
      <xsl:if test="position() != last()">,</xsl:if>
    </xsl:for-each>
  </fo:block>
</xsl:template>


<xsl:template match="p">
  <fo:block xsl:use-attribute-sets="paragraph">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>

<xsl:template match="body/p">
  <fo:block xsl:use-attribute-sets="paragraph-justified">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>
  
  <xsl:template match="body/sec/p">
    <fo:block xsl:use-attribute-sets="paragraph-justified">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="body/p[@content-type='alignright']">
    <fo:block xsl:use-attribute-sets="paragraph-right">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

  <xsl:template match="body/sec/p[@content-type='alignright']">
    <fo:block xsl:use-attribute-sets="paragraph-right">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>

<xsl:template match="body/p[@content-type='continuedparagraph']">
  <fo:block xsl:use-attribute-sets="paragraph-justified-noindent">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>
  
  <xsl:template match="body/sec/p[@content-type='continuedparagraph']">
    <fo:block xsl:use-attribute-sets="paragraph-justified-noindent">
      <xsl:apply-templates/>
    </fo:block>
  </xsl:template>


<xsl:template match="def[not(preceding-sibling::def)]/p[1]">
  <!-- matching the first p inside a first def -->
  <fo:block xsl:use-attribute-sets="paragraph-tight">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="permissions">
  <!-- allowed inside:
    app, array, article-meta, boxed-text, chem-struct-wrap,
    disp-quote, fig, front-stub, graphic, media, preformat,
    sec-meta, statement, supplementary-material, table-wrap,
    table-wrap-foot, verse-group
    -->
  <!-- content model:
    (copyright-statement*, copyright-year*, copyright-holder*,
     license*) -->
  <fo:block>
    <xsl:apply-templates select="copyright-statement"/>
    <xsl:if test="copyright-year | copyright-holder">
      <fo:block>
        <fo:inline xsl:use-attribute-sets="generated">Copyright </fo:inline>
        <xsl:for-each select="copyright-year | copyright-holder">
          <xsl:apply-templates/>
          <xsl:if test="not(position()=last())">
            <fo:inline xsl:use-attribute-sets="generated">, </fo:inline>
          </xsl:if>
        </xsl:for-each>
      </fo:block>
    </xsl:if>
    <xsl:apply-templates select="license"/>
  </fo:block>
</xsl:template>


<xsl:template name="notes">
  <xsl:call-template name="subsection-title">
    <xsl:with-param name="contents">
      <fo:wrapper xsl:use-attribute-sets="generated">Notes</fo:wrapper>
    </xsl:with-param>
  </xsl:call-template>
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="copyright-statement">
  <fo:block xsl:use-attribute-sets="copyright-line">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="license">
  <fo:block xsl:use-attribute-sets="license">
    <xsl:apply-templates/>
    <xsl:call-template name="append-doi-fop" />
  </fo:block>
</xsl:template>

<xsl:template name="append-doi-fop">
	<xsl:for-each select="/article/front/article-meta">
	  <xsl:variable name="contents" select="article-id"/>
	  DOI: <fo:basic-link external-destination="url('http://dx.doi.org/{$contents}')" xsl:use-attribute-sets="link">
	    http://dx.doi.org/<xsl:value-of select="$contents"/>
	  </fo:basic-link>
	  
	</xsl:for-each>
</xsl:template>

<xsl:template match="license-p">
  <fo:block>
        <xsl:attribute name="line-height">12pt</xsl:attribute>
        <xsl:attribute name="margin-top">10px</xsl:attribute>
        <xsl:attribute name="text-align">justify</xsl:attribute>
    <xsl:if test="not(preceding-sibling::license-p)">
      <fo:inline xsl:use-attribute-sets="generated">
        <xsl:text>License</xsl:text>
        <xsl:if
          test="../@license-type[normalize-space()] |
              ../@xlink:href[normalize-space()]">
          <xsl:text> (</xsl:text>
          <fo:inline xsl:use-attribute-sets="data">
            <xsl:value-of select="../@license-type"/>
            <xsl:if test="normalize-space(@xlink:href)">
              <xsl:if test="../@license-type">, </xsl:if>
              <xsl:call-template name="make-external-link">
                <xsl:with-param name="contents" select="@xlink:href"/>
              </xsl:call-template>
            </xsl:if>
          </fo:inline>
          <xsl:text>)</xsl:text>
        </xsl:if>
        <xsl:text>: </xsl:text>
      </fo:inline>
    </xsl:if>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<!-- ============================================================= -->
<!-- Figures, lists and block-level objects                        -->
<!-- ============================================================= -->


<xsl:template match="address">
  <xsl:choose>
    <!-- address appears as a sequence of inline elements if
         it has no addr-line and the parent may contain text -->
    <xsl:when
      test="not(addr-line) and
      (parent::collab | parent::p | parent::license-p |
       parent::named-content | parent::styled-content)">
      <xsl:call-template name="inline-address"/>
    </xsl:when>
    <xsl:otherwise>
      <fo:block xsl:use-attribute-sets="address">
        <xsl:apply-templates/>
      </fo:block>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<xsl:template name="inline-address">
  <!-- emits element children in a simple comma-delimited sequence -->
  <xsl:for-each select="*">
    <xsl:if test="position() &gt; 1">, </xsl:if>
    <xsl:apply-templates/>
  </xsl:for-each>
</xsl:template>


<xsl:template match="address/*" priority="2">
  <fo:block xsl:use-attribute-sets="address-line">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="address/email" priority="3">
  <fo:block xsl:use-attribute-sets="email address-line">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="address/ext-link" priority="3">
  <fo:block xsl:use-attribute-sets="ext-link address-line">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="address/uri" priority="3">
  <fo:block xsl:use-attribute-sets="address-line uri">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="alternatives">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="array">
  <fo:block xsl:use-attribute-sets="array">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>

<xsl:template match="disp-formula-group">
  <fo:block xsl:use-attribute-sets="disp-formula-group">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>

<xsl:template match="inline-graphic">
  <xsl:variable name="href">
    <xsl:call-template name="resolve-href"/>
  </xsl:variable>
  <fo:external-graphic src="url('{$href}')" content-width="auto"
    content-height="100%" scaling="uniform"/>
</xsl:template>


<xsl:template match="graphic | media">
  <xsl:param name="allow-float" select="true()"/>
  <xsl:variable name="href">
    <xsl:call-template name="resolve-href"/>
  </xsl:variable>
  <xsl:call-template name="set-float">
    <!-- graphics and media are only allowed to float
         when they appear outside the named elements -->
    <xsl:with-param name="allow-float"
      select="false()"/>
    <xsl:with-param name="contents">
      <fo:block-container xsl:use-attribute-sets="media-object">
        <xsl:apply-templates select="@orientation"/>
          <fo:block line-stacking-strategy="max-height">
            <fo:external-graphic src="url('{$href}')"
              content-width="scale-down-to-fit"
              scaling="uniform" width="100%"/>
            <xsl:apply-templates select="." mode="label"/>
            <xsl:apply-templates/>
          </fo:block>
      </fo:block-container>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<!--
$allow-float and
              not(ancestor::boxed-text | 

                  ancestor::chem-struct-wrap |
                  ancestor::disp-formula |
                  ancestor::fig | ancestor::fig-group |
                  ancestor::preformat |
                  ancestor::supplementary-material |

                  ancestor::table-wrap |
                  ancestor::table-wrap-group)

<xsl:template match="graphic | media">
  <xsl:param name="allow-float" select="true()"/>
  <xsl:variable name="href">
    <xsl:call-template name="resolve-href"/>
  </xsl:variable>
  <xsl:call-template name="set-float">
   graphics and media are only allowed to float
         when they appear outside the named elements
    <xsl:with-param name="allow-float"
      select="false"/>
    <xsl:with-param name="contents">
      <fo:block-container xsl:use-attribute-sets="media-object">
        <xsl:apply-templates select="@orientation"/>
        <fo:wrapper start-indent="0pc">
          <fo:block line-stacking-strategy="max-height">
            <fo:external-graphic src="url('{$href}')"
              content-width="scale-down-to-fit"
              scaling="uniform" width="100%"/>
            <xsl:apply-templates select="." mode="label"/>
            <xsl:apply-templates/>
          </fo:block>
        </fo:wrapper>
      </fo:block-container>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>
-->

<xsl:template match="alt-text">
  <!-- not handled with graphic or inline-graphic -->
</xsl:template>


<xsl:template match="author-notes">
  <fo:block xsl:use-attribute-sets="author-notes">
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="fn-group">
  <fo:block xsl:use-attribute-sets="fn-group">
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="long-desc">
  <fo:block xsl:use-attribute-sets="long-desc">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="open-access">
  <fo:block xsl:use-attribute-sets="open-access">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="sig-block">
  <fo:block xsl:use-attribute-sets="sig-block">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="attrib">
  <fo:block xsl:use-attribute-sets="attrib">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<!-- floating objects include 
   boxed-text, chem-struct-wrap, fig, fig-group, graphic,
   media, preformat, supplementary-material, table-wrap,
   table-wrap-group -->


<xsl:template match="boxed-text">
  <xsl:param name="allow-float" select="true()"/>
  <xsl:call-template name="set-float">
    <xsl:with-param name="allow-float" select="$allow-float"/>
    <xsl:with-param name="contents">
      <fo:block-container xsl:use-attribute-sets="boxed-text">
        <xsl:apply-templates select="@orientation"/>
        <fo:wrapper start-indent="0pc">
          <xsl:apply-templates select="." mode="label"/>
          <xsl:apply-templates/>
        </fo:wrapper>
      </fo:block-container>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="chem-struct-wrap">
  <xsl:param name="allow-float" select="true()"/>
  <xsl:call-template name="set-float">
    <xsl:with-param name="allow-float" select="$allow-float"/>
    <xsl:with-param name="contents">
      <fo:block-container xsl:use-attribute-sets="chem-struct-box">
        <xsl:apply-templates select="@orientation"/>
        <fo:wrapper start-indent="0pc">
          <xsl:apply-templates select="." mode="label"/>
          <xsl:apply-templates/>
        </fo:wrapper>
      </fo:block-container>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="chem-struct-wrap/chem-struct">
  <fo:block xsl:use-attribute-sets="chem-struct">
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>

<xsl:template match="fig | fig-group">
          <xsl:apply-templates/>
</xsl:template>


<xsl:template match="fig-group/fig">
  <fo:block xsl:use-attribute-sets="fig">
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="supplementary-material">
  <xsl:param name="allow-float" select="true()"/>
  <xsl:call-template name="set-float">
    <xsl:with-param name="allow-float" select="$allow-float"/>
    <xsl:with-param name="contents">
      <fo:block-container xsl:use-attribute-sets="supplementary">
        <xsl:apply-templates select="@orientation"/>
        <fo:wrapper start-indent="0pc">
          <xsl:apply-templates select="." mode="label"/>
          <xsl:apply-templates/>
        </fo:wrapper>
      </fo:block-container>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="table-wrap | table-wrap-group">
  
      <fo:block-container xsl:use-attribute-sets="table-box">
          <xsl:if test=".//table[@width='100%']">
            <xsl:attribute name="start-indent">0pc</xsl:attribute>
          </xsl:if>

        <xsl:apply-templates select="@orientation"/>
        
          <xsl:apply-templates/>
          <xsl:apply-templates mode="footnote"
            select="self::table-wrap//fn[not(ancestor::table-wrap-foot)]"/>
      </fo:block-container>
</xsl:template>


<xsl:template match="table-wrap-group/table-wrap">
  <fo:block xsl:use-attribute-sets="table-wrap">
    <xsl:call-template name="assign-id"/>
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
    <xsl:apply-templates mode="footnote"
      select=".//fn[not(ancestor::table-wrap-foot)]"/>
  </fo:block>
</xsl:template>


<xsl:template match="table-wrap-foot">
  <fo:block xsl:use-attribute-sets="table-wrap-foot">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="caption">
  <fo:block xsl:use-attribute-sets="caption">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="disp-formula">
  <fo:block xsl:use-attribute-sets="disp-formula">
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="disp-quote">
  <fo:block xsl:use-attribute-sets="disp-quote">
    <xsl:call-template name="assign-id"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="preformat">
  <xsl:param name="allow-float" select="false()"/>
  <xsl:call-template name="set-float">
    <xsl:with-param name="allow-float"
      select="$allow-float and
        not(ancestor::bio | ancestor::boxed-text | ancestor::chem-struct |
            ancestor::chem-struct-wrap | ancestor::disp-formula |
            ancestor::disp-quote | ancestor::fig | ancestor::glossary |
            ancestor::supplementary-material | 
            ancestor::disp-formula | ancestor::table-wrap)"/>
    <xsl:with-param name="contents">
        <xsl:apply-templates select="@orientation"/>
          <fo:block xsl:use-attribute-sets="preformat">
        <xsl:apply-templates/>
          </fo:block>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="@orientation">
  <xsl:if test=".='landscape'">
    <xsl:attribute name="reference-orientation">90</xsl:attribute>
    <xsl:attribute name="width">4in</xsl:attribute>
  </xsl:if>
</xsl:template>


<xsl:template match="table-wrap-group/@orientation |
  table-wrap/@orientation">
  <xsl:if test=".='landscape'">
    <xsl:attribute name="reference-orientation">90</xsl:attribute>
    <xsl:attribute name="width">6in</xsl:attribute>
  </xsl:if>
</xsl:template>


<xsl:template match="textual-form">
  <fo:block xsl:use-attribute-sets="textual-form">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="speech">
  <fo:block xsl:use-attribute-sets="speech">
    <xsl:apply-templates mode="speech"/>
  </fo:block>
</xsl:template>


<xsl:template match="speech/speaker" mode="speech"/>


<xsl:template match="speech/p" mode="speech">
  <fo:block xsl:use-attribute-sets="paragraph">
    <xsl:apply-templates
      select="self::p[not(preceding-sibling::p)]/../speaker"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="speech/speaker">
  <xsl:call-template name="bold"/>
  <fo:inline xsl:use-attribute-sets="generated">: </fo:inline>
</xsl:template>


<xsl:template match="statement">
  <fo:block xsl:use-attribute-sets="statement">
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="verse-group">
  <fo:block-container xsl:use-attribute-sets="verse">
    <fo:wrapper start-indent="0pc">
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates/>
    </fo:wrapper>
  </fo:block-container>
</xsl:template>


<xsl:template match="verse-line">
  <fo:block xsl:use-attribute-sets="verse-line">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="def-list">
  <fo:block xsl:use-attribute-sets="def-list">
    <xsl:apply-templates select="." mode="label"/>
    <!-- content model is
       (label?, title?, term-head?, def-head?, def-item*, def-list*)-->
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="def-list/def-list">
  <fo:block xsl:use-attribute-sets="sub-def-list">
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="term-head">
  <xsl:call-template name="def-list-head"/>
</xsl:template>


<xsl:template match="def-head">
  <!-- def-head makes a line only if it is not accompanied
       by a term-head; if it is, it's already been done -->
  <xsl:if test="not(preceding-sibling::term-head)">
    <xsl:call-template name="def-list-head"/>
  </xsl:if>
</xsl:template>


<xsl:template name="def-list-head">
  <!-- The calling context is either a term-head or a def-head
       (the latter only if there is no term-head); this
       makes a line containing either or both, positioning
       each correctly -->
  <fo:block xsl:use-attribute-sets="def-list-head">
    <fo:inline xsl:use-attribute-sets="term-head">
      <xsl:apply-templates mode="def-list-head" select="self::term-head"/>
    </fo:inline>
    <fo:inline xsl:use-attribute-sets="def-head">
      <xsl:apply-templates mode="def-list-head"
        select="self::def-head | following-sibling::def-head"/>
    </fo:inline>
  </fo:block>
</xsl:template>


<xsl:template match="term-head | def-head" mode="def-list-head">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="def-item">
  <fo:block xsl:use-attribute-sets="def-item">
    <!-- content model is (term, def*) -->
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="term">
  <fo:block xsl:use-attribute-sets="def-list-term">
    <xsl:apply-templates select="parent::def-item" mode="label-text"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="def">
  <fo:block xsl:use-attribute-sets="def-list-def">
    <!-- content model is (term, def*) -->
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="list">
  <fo:block xsl:use-attribute-sets="list">
    <xsl:call-template name="make-list"/>
  </fo:block>
</xsl:template>


<xsl:template match="list//list">
  <fo:block xsl:use-attribute-sets="sub-list">
    <xsl:call-template name="make-list"/>
  </fo:block>
</xsl:template>


<xsl:template name="make-list">
  <xsl:call-template name="assign-id"/>
  <xsl:apply-templates select="." mode="label"/>
  <xsl:apply-templates select="title"/>

  <xsl:variable name="start-to-start">
    <xsl:variable name="marker-allowance">
      <xsl:choose>
        <xsl:when test="@list-type='simple'">0</xsl:when>
        <xsl:when test="@list-type='bullet' or not(@list-type)">10</xsl:when>
        <xsl:when test="@list-type='roman-upper' or @list-type='roman-lower'"
          >36</xsl:when>
        <xsl:otherwise>18</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="prefix-allowance"
      select="string-length(@prefix-word) * 6"/>
    <xsl:value-of select="$marker-allowance + $prefix-allowance"/>
  </xsl:variable>
  <xsl:variable name="end-to-start">
    <xsl:choose>
      <xsl:when test="not(@list-type='simple')">6</xsl:when>
      <xsl:otherwise>0</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  <fo:list-block provisional-distance-between-starts="{$start-to-start}pt"
    provisional-label-separation="{$end-to-start}pt">
    <xsl:apply-templates select="list-item"/>
  </fo:list-block>
</xsl:template>


<xsl:template match="list-item">
  <fo:list-item xsl:use-attribute-sets="list-item">
    <xsl:call-template name="assign-id"/>
    <fo:list-item-label end-indent="label-end()">
      <fo:block xsl:use-attribute-sets="list-item-label">
        <xsl:apply-templates select="." mode="label-text"/>
      </fo:block>
    </fo:list-item-label>
    <fo:list-item-body start-indent="body-start()">
      <xsl:apply-templates/>
    </fo:list-item-body>
  </fo:list-item>
</xsl:template>


<!-- ============================================================= -->
<!-- Tables                                                        -->
<!-- ============================================================= -->


<xsl:include href="xhtml-tables-fo.xsl"/>


<!-- ============================================================= -->
<!-- Inline elements                                               -->
<!-- ============================================================= -->


<xsl:template match="abbrev">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="abbrev/def">
  <xsl:text>[</xsl:text>
  <xsl:apply-templates/>
  <xsl:text>]</xsl:text>
</xsl:template>

<xsl:template
  match="p/address | license-p/address |
  named-content/p | styled-content/p">
  <xsl:apply-templates mode="inline"/>
</xsl:template>


<xsl:template match="address/*" mode="inline">
  <xsl:if test="preceding-sibling::*">
    <fo:inline xsl:use-attribute-sets="generated">, </fo:inline>
  </xsl:if>
  <xsl:apply-templates/>
</xsl:template>

<xsl:template match="addr-line | country | fax | 
                       institution | phone">
  <xsl:if test="preceding-sibling::*">
    <xsl:text> </xsl:text>
  </xsl:if>
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="award-id">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="break">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="email">
  <fo:inline xsl:use-attribute-sets="email">
    <xsl:apply-templates/>
  </fo:inline>
</xsl:template>


<xsl:template
  match="article-meta/email | contrib-group/email |
                contrib/email | array/email | 
                chem-struct-wrap/email | fig-group/email | 
                fig/email | graphic/email | media/email |
                supplementary-material/email |
                table-wrap-group/email | table-wrap/email |
                disp-formula-group/email | front-stub/email">
  <fo:block xsl:use-attribute-sets="email">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="ext-link | uri | inline-supplementary-material">
  <xsl:call-template name="make-external-link"/>
</xsl:template>

<xsl:template match="fn-link">
  <xsl:call-template name="make-internal-link"/>
</xsl:template>


<xsl:template match="array/ext-link | chem-struct-wrap/ext-link |
                     fig-group/ext-link | fig/ext-link |
                     graphic/ext-link | media/ext-link |
                     supplementary-material/ext-link |
                     table-wrap-group/ext-link | table-wrap/ext-link |
                     disp-formula-group/ext-link">
  <fo:block xsl:use-attribute-sets="ext-link">
    <xsl:call-template name="make-external-link"/>
  </fo:block>
</xsl:template>


<xsl:template match="array/uri | chem-struct-wrap/uri |
                     fig-group/uri | fig/uri |
                     graphic/uri | media/uri |
                     supplementary-material/uri |
                     table-wrap-group/uri |
                     table-wrap/uri | disp-formula-group/uri">
  <fo:block xsl:use-attribute-sets="uri">
    <xsl:call-template name="make-external-link"/>
  </fo:block>
</xsl:template>


<xsl:template match="funding-source">
  <fo:inline xsl:use-attribute-sets="funding-source">
    <xsl:apply-templates/>
  </fo:inline>
</xsl:template>


<xsl:template match="hr">
  <fo:block border-top="thin solid black"/>
</xsl:template>


<xsl:template match="inline-formula">
  <fo:inline xsl:use-attribute-sets="inline-formula">
    <xsl:apply-templates/>
  </fo:inline>
</xsl:template>


<xsl:template match="milestone-start | milestone-end"/>
<!-- suppressed in this application -->


<xsl:template match="object-id">
  <fo:block xsl:use-attribute-sets="object-id">
    <fo:inline xsl:use-attribute-sets="generated">Object ID: </fo:inline>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="sig">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="target">
  <fo:inline>
    <xsl:call-template name="assign-id"/>
  </fo:inline>
</xsl:template>


<xsl:template match="private-char">
  <fo:inline xsl:use-attribute-sets="generated">[Private character</fo:inline>
  <xsl:for-each select="@name">
    <xsl:text> </xsl:text>
    <xsl:value-of select="."/>
  </xsl:for-each>
  <fo:inline xsl:use-attribute-sets="generated">]</fo:inline>
</xsl:template>


<xsl:template match="glyph-data | glyph-ref">
  <fo:inline xsl:use-attribute-sets="generated">(Glyph not
    rendered)</fo:inline>
</xsl:template>


<xsl:template match="related-article">
  <fo:inline xsl:use-attribute-sets="generated">[Related article:] </fo:inline>
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="related-object">
  <fo:inline xsl:use-attribute-sets="generated">[Related object:] </fo:inline>
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="bold">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="chem-struct">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="italic">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="monospace">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="named-content">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="overline">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="roman">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="sans-serif">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="sc">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="strike">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="styled-content">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="sub">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="sup">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<xsl:template match="underline">
  <xsl:apply-templates select="." mode="format"/>
</xsl:template>


<!-- ============================================================= -->
<!-- Back matter                                                   -->
<!-- ============================================================= -->

<xsl:template match="back">
  <!-- content model for back: 
        (label?, title*, 
        (ack | app-group | bio | fn-group | glossary | ref-list |
        notes | sec)*) -->
  <fo:block xsl:use-attribute-sets="back">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="ack">
  <xsl:call-template name="backmatter-section">
    <xsl:with-param name="generated-title">Acknowledgements</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="app-group">
  <xsl:call-template name="backmatter-section">
    <xsl:with-param name="generated-title">Appendices</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="app">
  <fo:block xsl:use-attribute-sets="app">
    <xsl:call-template name="assign-id"/>
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="ref-list">
  <fo:block xsl:use-attribute-sets="ref-list-section">
    <xsl:call-template name="assign-id"/>
    <xsl:apply-templates select="." mode="label"/>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="ref">
  <xsl:if test="not(preceding-sibling::ref)">
    <!-- a list is made, but only for the first ref, which
         pulls all the rest; the ref-list content model
         ensures they are contiguous -->
    <fo:list-block xsl:use-attribute-sets="ref-list-block">
      <xsl:for-each select=".|following-sibling::ref">
        <fo:list-item xsl:use-attribute-sets="ref-list-item">
          <xsl:call-template name="assign-id"/>
          <fo:list-item-label end-indent="label-end()">
            <fo:block xsl:use-attribute-sets="list-item-label">
              <!--<xsl:apply-templates select="." mode="label"/>-->
            </fo:block>
          </fo:list-item-label>
          <fo:list-item-body start-indent="body-start()">
            <fo:block-container>
              <!-- extra circumlocutions are necessary to redefine
                   the reference area for indenting -->

            <fo:block xsl:use-attribute-sets="ref">
              <xsl:apply-templates/>
            </fo:block>

            </fo:block-container>
          </fo:list-item-body>
        </fo:list-item>
      </xsl:for-each>
    </fo:list-block>
  </xsl:if>
</xsl:template>


<xsl:template match="back/bio">
  <xsl:call-template name="backmatter-section">
    <xsl:with-param name="generated-title">Biography</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="back/fn-group">
  <xsl:call-template name="backmatter-section">
    <xsl:with-param name="generated-title">End notes</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="back/glossary">
  <xsl:call-template name="backmatter-section">
    <xsl:with-param name="generated-title">Glossary</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="back/ref-list">
  <xsl:call-template name="backmatter-section">
    <xsl:with-param name="generated-title">References</xsl:with-param>
    <xsl:with-param name="contents">
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="back/notes">
  <xsl:call-template name="backmatter-section">
    <xsl:with-param name="generated-title">Notes</xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template name="backmatter-section">
  <xsl:param name="generated-title"/>
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:block xsl:use-attribute-sets="back-section">
    <xsl:call-template name="assign-id"/>
    <xsl:if test="not(title) and $generated-title">
      <xsl:choose>
        <!-- The level of title depends on whether the back matter itself
             has a title -->
        <xsl:when test="ancestor::back/title">
          <xsl:call-template name="section-title">
            <xsl:with-param name="contents" select="$generated-title"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="main-title">
            <xsl:with-param name="contents" select="$generated-title"/>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
    <xsl:copy-of select="$contents"/>
  </fo:block>
</xsl:template>


<!-- ============================================================= -->
<!-- Floats group                                                  -->
<!-- ============================================================= -->

<xsl:template match="floats-group">
  <xsl:apply-templates mode="floats"/>
</xsl:template>


<xsl:template match="alternatives" mode="floats">
  <xsl:apply-templates mode="floats"/>
</xsl:template>


<xsl:template match="*" mode="floats">
  <!-- floats are rendered in place unless they are both 
       cross-referenced somewhere by an xref, and they have
       do not have @position != "float", in which case
       they have been floated to near the point of the xref -->
  <xsl:variable name="xrefs" select="key('xref-by-rid',@id)"/>
  <xsl:choose>
     <xsl:when test="boolean($xrefs) and not(@position != 'float')"/>
     <xsl:otherwise>
       <xsl:apply-templates select=".">
         <xsl:with-param name="allow-float" select="false()"/>
       </xsl:apply-templates>
     </xsl:otherwise>
  </xsl:choose>
  
</xsl:template>

    
<!-- ============================================================= -->
<!-- Citation content                                              -->
<!-- ============================================================= -->
<!-- Citations should have been pre-processed; citation formatting
   is not supported by this stylesheet.                          -->


<xsl:template match="mixed-citation | element-citation |
                     nlm-citation | related-article |
                     related-object | product">
  <fo:block xsl:use-attribute-sets="citation">
    <xsl:apply-templates/>    
  </fo:block>
</xsl:template>

<xsl:template match="mixed-citation//* |
                     related-article//* |
                     product//* |
                     related-object//*"
  priority="-0.25">
  <!-- descendants of these elements with better matches will be
       processed by their regular templates due to the priority -->
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="element-citation//*" priority="1">
  <!-- this template, however, overrides other templates matching
       the same elements -->
  <xsl:apply-templates/>
  <xsl:if
    test="not(generate-id() =
    generate-id(ancestor::element-citation/descendant::*[last()]))">
    <xsl:text> </xsl:text>
  </xsl:if>
</xsl:template>



<!-- ============================================================= -->
<!-- Footnotes and cross-references                                -->
<!-- ============================================================= -->
<!-- Cross-references are passed through except when they
   have no content, in which case:
   
   1. if they point to an fn-group/fn, or to an fn that appears
      before them, they acquire the footnote label
   2. if not, they acquire the label of the element to which they
      point
   3. if no such label is available, they generate an error label -->


<xsl:template match="fn-group/fn | author-notes/fn |
                     author-notes/corresp | table-wrap-foot//fn">
  <fo:block xsl:use-attribute-sets="endnote">
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="fn">
  <!-- matching fn elements not inside fn-group or author-notes -->
  <xsl:variable name="xrefs" select="key('xref-by-rid',@id)"/>
  <xsl:choose>
    <!-- if the fn is referenced only by xrefs that appear after
         it, we generate the footnote here -->
    <xsl:when test="generate-id() = generate-id((.|$xrefs)[1])">
      <xsl:apply-templates select="." mode="format"/>
    </xsl:when>
    <xsl:otherwise>
      <fo:inline xsl:use-attribute-sets="footnote-ref">
        <xsl:apply-templates mode="fn-ref-punctuate"
          select="preceding-sibling::node()[1]"/>
        <xsl:apply-templates select="." mode="label-text">
          <!-- we want a warning only if an xref exists -->
          <xsl:with-param name="warning" select="true()"/>
        </xsl:apply-templates>
      </fo:inline>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<xsl:template match="fn | aff | corresp" mode="fn-ref-punctuate">
  <!-- if a footnote ref is directly preceded by a footnote
       ref, we need punctuation -->
  <xsl:text>,</xsl:text>
</xsl:template>


<xsl:template match="xref" mode="fn-ref-punctuate">
  <xsl:variable name="target" select="key('element-by-id',@rid)"/>
  <!-- likewise if it is directly preceded by an xref
  to a footnote -->
  <xsl:if test="$target[self::fn | self::aff | self::corresp]">
    <xsl:text>,</xsl:text>
  </xsl:if>
</xsl:template>


<xsl:template match="* | text()" mode="fn-ref-punctuate"/>
<!-- no punctuation for any other directly preceding sibling -->


<xsl:template match="text()[not(normalize-space())] |
                     comment() | processing-instruction()"
              mode="fn-ref-punctuate">
  <!-- but for whitespace-only text nodes, comments and
       PIs, we have to keep looking -->
  <xsl:apply-templates mode="fn-ref-punctuate"
          select="preceding-sibling::node()[1]"/>
</xsl:template>


<xsl:template name="fn-xref">
  <xsl:param name="target" select="key('element-by-id',@rid)"/>
  <xsl:param name="xrefs" select="key('xref-by-rid',@rid)"/>
  <xsl:variable name="symbol">
    <xsl:apply-templates mode="fn-ref-punctuate"
      select="preceding-sibling::node()[1]"/>
    <xsl:apply-templates/>
    <xsl:if test="not(normalize-space())">
      <xsl:apply-templates select="$target" mode="label-text">
        <xsl:with-param name="warning" select="true()"/>
      </xsl:apply-templates>
    </xsl:if>
  </xsl:variable>

  <xsl:choose>
    <!-- Any of several conditions result in placing a
         footnote reference but not an actual footnote here;
         if all fail, we place a footnote along with
         the xref that references it. -->
    <!-- We have only the reference if the fn target has a
         parent fn-group or table-wrap-foot (the footnote
         text appears at the point of the fn). -->
    <xsl:when test="$target/parent::fn-group |   
                    $target[ancestor::table-wrap-foot]">
      <fo:inline xsl:use-attribute-sets="footnote-ref">
        <xsl:copy-of select="symbol"/>
      </fo:inline>
    <!-- We have only the reference if the fn target is
         inside article-meta (the footnote text appears 
         elsewhere). -->
    </xsl:when>
    <xsl:when test="$target/ancestor::article-meta">
      <fo:inline xsl:use-attribute-sets="footnote-ref">
        <xsl:copy-of select="symbol"/>
      </fo:inline>
    </xsl:when>
    <!-- We have only the reference if the fn target is
         also targetted by an earlier xref (the footnote
         should appear there), or if the footnote itself
         appears earlier (and not inside fn-group or
         table-wrap-foot, caught above). -->
    <xsl:when test="not(generate-id() = generate-id(($target|$xrefs)[1]))">
      <fo:inline xsl:use-attribute-sets="footnote-ref">
        <xsl:copy-of select="symbol"/>
      </fo:inline>
    </xsl:when>
    <!-- Otherwise we get the reference and the footnote. --> 
    <xsl:otherwise>
      <xsl:call-template name="make-footnote">
        <xsl:with-param name="symbol">
          <xsl:copy-of select="symbol"/>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<xsl:template match="xref">
  <xsl:variable name="target" select="key('element-by-id',@rid)"/>
  <xsl:variable name="xrefs" select="key('xref-by-rid',@rid)"/>
  <xsl:variable name="fn-number">
    <xsl:number level="any" count="xref[not(ancestor::front) and @ref-type='fn']"
      from="article | sub-article | response"/>
  </xsl:variable>
  <xsl:choose>
    <!-- if the xref points to an fn, aff or corresp we
         call out to 'fn-xref' -->
    <xsl:when test="$target[self::aff | self::corresp]">
      <xsl:call-template name="fn-xref">
        <xsl:with-param name="target" select="$target"/>
        <xsl:with-param name="xrefs" select="$xrefs"/>
      </xsl:call-template>
    </xsl:when>
    <!-- this handles auto footnotes -->
    <xsl:when test="@ref-type='fn'">
      <!-- this is an auto-numbered footnote -->
      <fo:basic-link internal-destination="fn{$fn-number}" id="xr{$fn-number}">
        <fo:inline xsl:use-attribute-sets="link footnote-ref"><xsl:copy-of select="$fn-number"/></fo:inline>
      </fo:basic-link>
    </xsl:when>
    <xsl:when test="@ref-type='bibr'">
      <xsl:variable name="selfid" select="@id"/>
      <xsl:variable name="rid" select="@rid"/>
      <!-- this is an auto-numbered footnote -->
      <fo:basic-link internal-destination="{$rid}" id="link{$selfid}">
        <fo:inline xsl:use-attribute-sets="link"><xsl:apply-templates/></fo:inline>
      </fo:basic-link>
    </xsl:when>
    <!-- otherwise, we place either the xref content, or an
         acquired label (if we have no content) here -->
    <xsl:otherwise>
      <fo:inline xsl:use-attribute-sets="xref">
        <xsl:choose>
          <xsl:when test="normalize-space()">
            <xsl:apply-templates/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates select="$target" mode="label-text">
              <xsl:with-param name="warning" select="true()"/>
            </xsl:apply-templates>
          </xsl:otherwise>
        </xsl:choose>
      </fo:inline>
      <!-- now, if the target is directly inside floats-group,
           does not have @position or @position='float', and 
           this is the first xref to it, we grab it and place it here -->
      <xsl:if
        test="$target[not(@position != 'float')]
              /parent::floats-group and
              generate-id() = generate-id($xrefs[1])">
        <xsl:apply-templates select="$target"/>
      </xsl:if>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<xsl:template match="fn" mode="format">
  <xsl:call-template name="make-footnote">
    <xsl:with-param name="symbol">
      <xsl:apply-templates select="." mode="label-text">
        <xsl:with-param name="warning" select="true()"/>
      </xsl:apply-templates>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template name="make-footnote">
  <xsl:param name="symbol"/>
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:footnote>
    <fo:inline xsl:use-attribute-sets="footnote-ref">
      <xsl:apply-templates mode="fn-ref-punctuate"
          select="preceding-sibling::node()[1]"/>
        <xsl:copy-of select="$symbol"/>
    </fo:inline>
    <fo:footnote-body xsl:use-attribute-sets="footnote-body">
      <xsl:copy-of select="$contents"/>
    </fo:footnote-body>
  </fo:footnote>
</xsl:template>


<xsl:template match="fn/p">
  <fo:block xsl:use-attribute-sets="paragraph">
    <xsl:call-template name="assign-id"/>
    <xsl:if test="not(preceding-sibling::p)">
      <xsl:apply-templates select="parent::fn" mode="label-text"/>
      <xsl:text> </xsl:text>
    </xsl:if>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<xsl:template match="fn-group/fn/p | author-notes/fn/p |
  table-wrap//fn/p" priority="2">
  <xsl:variable name="empty-xrefs"
    select="key('xref-by-rid',../@id)[not(normalize-space())]"/>
  <fo:block xsl:use-attribute-sets="paragraph">
    <xsl:call-template name="assign-id"/>
    <xsl:if test="not(preceding-sibling::p)">
      <xsl:variable name="label">
        <xsl:apply-templates select="parent::fn" mode="label-text">
          <!-- we want a warning only if an empty xref exists -->
          <xsl:with-param name="warning" select="boolean($empty-xrefs)"/>
        </xsl:apply-templates>
      </xsl:variable>
      <xsl:copy-of select="$label"/>
      <xsl:if test="normalize-space($label)">
        <xsl:if test="not(contains($label,']'))">.</xsl:if>
        <xsl:text> </xsl:text>
      </xsl:if>
    </xsl:if>
    <xsl:apply-templates/>
  </fo:block>
</xsl:template>


<!-- ============================================================= -->
<!-- Mode "format"                                                 -->
<!-- ============================================================= -->
<!-- Provides for generic formatting of inline elements.
     Templates in this mode are also named, so they may be
     called for other elements as well.                           -->


<xsl:template match="*" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:copy-of select="$contents"/>
</xsl:template>


<xsl:template name="bold" match="bold" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline font-weight="bold">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="break" match="break" mode="format">
  <fo:block/>
</xsl:template>

<xsl:template name="chem-struct" match="chem-struct" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline xsl:use-attribute-sets="chem-struct-inline">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="italic" match="italic" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  
  <xsl:choose>
    <xsl:when test="count(ancestor::italic) mod 2 = 1">
      <fo:inline font-style="normal">
        <xsl:copy-of select="$contents"/>
      </fo:inline>
    </xsl:when>
    <xsl:otherwise>
      <fo:inline font-style="italic">
        <xsl:copy-of select="$contents"/>
      </fo:inline>    
    </xsl:otherwise>
  </xsl:choose>  
</xsl:template>


<xsl:template name="monospace" match="monospace" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline xsl:use-attribute-sets="monospace">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="named-content" match="named-content" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:copy-of select="$contents"/>
</xsl:template>


<xsl:template name="overline" match="overline" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline text-decoration="overline">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="roman" match="roman" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline font-style="normal">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="sans-serif" match="sans-serif" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline xsl:use-attribute-sets="sans-serif">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="sc" match="sc" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline font-variant="small-caps">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="strike" match="strike" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline text-decoration="line-through">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="styled-content" match="styled-content" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline>
    <xsl:call-template name="process-style">
      <xsl:with-param name="style" select="@style"/>
    </xsl:call-template>
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="sub" match="sub" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline xsl:use-attribute-sets="subscript">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="sup" match="sup" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline xsl:use-attribute-sets="superscript">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>


<xsl:template name="underline" match="underline" mode="format">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:inline text-decoration="underline">
    <xsl:copy-of select="$contents"/>
  </fo:inline>
</xsl:template>



<!-- ============================================================= -->
<!-- Mode "label"                                                  -->
<!-- ============================================================= -->
<!-- Acquires or generates a label for any object.                 -->


<xsl:template mode="label" match="*" name="block-label">
  <xsl:param name="contents">
    <xsl:apply-templates select="." mode="label-text">
      <!-- we place a warning for missing labels if this element is ever
           cross-referenced with an empty xref -->
      <xsl:with-param name="warning"
        select="boolean(key('xref-by-rid',@id)[not(normalize-space())])"/>
    </xsl:apply-templates>
  </xsl:param>
  <xsl:if test="normalize-space($contents)">
    <fo:block xsl:use-attribute-sets="label">
      <xsl:copy-of select="$contents"/>
    </fo:block>
  </xsl:if>
</xsl:template>


<xsl:template mode="label" match="ref">
  <!-- labels for 'ref' are formatted as run-ins -->
  <xsl:param name="contents">
    <xsl:apply-templates select="." mode="label-text"/>
  </xsl:param>
  <xsl:if test="normalize-space($contents)">
    <!-- we're already in a p -->
    <fo:inline xsl:use-attribute-sets="label">
      <xsl:copy-of select="$contents"/>
    </fo:inline>
  </xsl:if>
</xsl:template>


<xsl:template name="set-outset-label">
  <!-- labels for sections and occasionally other stuff
       need to be set outside the body column -->
  <xsl:variable name="empty-xrefs"
    select="key('xref-by-rid',@id)[not(normalize-space())]"/>
  <xsl:variable name="label">
    <xsl:apply-templates select="." mode="label-text">
      <xsl:with-param name="warning" select="boolean($empty-xrefs)"/>
    </xsl:apply-templates>
  </xsl:variable>
  <xsl:if test="normalize-space($label)">
    <fo:block xsl:use-attribute-sets="label outset">
      <xsl:copy-of select="$label"/>
    </fo:block>
  </xsl:if>
</xsl:template>


<!-- ============================================================= -->
<!-- Mode "label-text"                                             -->
<!-- ============================================================= -->
<!-- Generates label text for elements and their cross-references


      This mode is to support auto-numbering for any elements
      by the stylesheet.

      Code is left in place (although not used) to autonumber
      several elements, such as figures and tables. -->


<!-- Variable declarations switch autonumbering on and off.
     In some cases, elements are autolabeled on a case-by-case
     basis (such as footnotes, which are allowed to be
     unlabeled in some cases but require autolabeling in others;
     these variables, in contrast, are intended to switch
     labelling for entire element classes. -->
  
<xsl:variable name="auto-label-app" select="false()"/>
<xsl:variable name="auto-label-boxed-text" select="false()"/>
<xsl:variable name="auto-label-chem-struct-wrap" select="false()"/>
<xsl:variable name="auto-label-disp-formula" select="false()"/>
<xsl:variable name="auto-label-fig" select="false()"/>
<xsl:variable name="auto-label-sec" select="false()"/>

<xsl:variable name="auto-label-ref" select="not(//ref[label])"/>
<!-- ref elements are labeled unless any ref already has a label -->

<xsl:variable name="auto-label-statement" select="false()"/>
<xsl:variable name="auto-label-supplementary" select="false()"/>
<xsl:variable name="auto-label-table-wrap" select="false()"/>

<!--
  The following (commented) variable assignments show how 
    autolabeling can be configured conditionally.
  For example: "label figures if no figures have labels" translates to
    "not(//fig[label])", which will resolve to Boolean true() when the set of
  all fig elements with labels is empty.

<xsl:variable name="auto-label-app" select="not(//app[label])"/>
<xsl:variable name="auto-label-boxed-text" select="not(//boxed-text[label])"/>
<xsl:variable name="auto-label-chem-struct-wrap" select="not(//chem-struct-wrap[label])"/>
<xsl:variable name="auto-label-disp-formula" select="not(//disp-formula[label])"/>
<xsl:variable name="auto-label-fig" select="not(//fig[label])"/>
<xsl:variable name="auto-label-ref" select="not(//ref[label])"/>
<xsl:variable name="auto-label-statement" select="not(//statement[label])"/>
<xsl:variable name="auto-label-supplementary"
  select="not(//supplementary-material[not(ancestor::front)][label])"/>
<xsl:variable name="auto-label-table-wrap" select="not(//table-wrap[label])"/>

-->

<!-- Mode "label-text" templates follow a pattern. Parameters (which
     may be assigned by default but are occasionally overridden by
     calling templates) determine:
       - Whether an element may be autolabeled;
       - If so, how to construct its label;
       - Whether to emit a warning label if no label is available.

     In all cases, a label given with an element (or in the case
     of 'fn', a @symbol) will be used in preference to a generated
     label. A warning will be generated only if $warning is
     true, $auto-label-x if false, and there is no label or
     @symbol available in the source document. -->
  
<xsl:template match="aff" mode="label-text">
  <xsl:param name="warning" select="false()"/>
  <xsl:variable name="empty-xrefs" select="key('xref-by-rid',@id)[not(normalize-space())]"/>
  <!-- auto-number this aff if it has any empty xrefs -->
  <xsl:variable name="auto-label-aff" select="boolean($empty-xrefs)"/>
  <!-- pass $warning in as false() if a warning string is not wanted
       (for example, if generating autonumbered labels) -->
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-aff"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <!-- counting only affs that have empty xrefs -->
      <xsl:number format="(a)" count="aff[key('xref-by-rid',@id)[not(normalize-space())]]"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="app" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-app"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>Appendix </xsl:text>
      <xsl:number format="A"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="boxed-text" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-boxed-text"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>Box </xsl:text>
      <xsl:number level="any"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="disp-formula" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-disp-formula"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>Formula </xsl:text>
      <xsl:number level="any"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="chem-struct-wrap" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-chem-struct-wrap"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>Formula (chemical) </xsl:text>
      <xsl:number level="any"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="fig" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-fig"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>Figure </xsl:text>
      <xsl:number level="any"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="fn" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <!-- autonumber all fn elements outside fn-group
       author-notes and table-wrap only if none of them 
       have labels or @symbols (to keep numbering
       orderly) -->
  <xsl:variable name="in-scope-notes"
    select="ancestor::article//fn[not(parent::fn-group
                                | parent::author-notes
                                | ancestor::table-wrap)]"/>
  <xsl:variable name="auto-number-fn"
    select="not($in-scope-notes/label |
                $in-scope-notes/@symbol)"/>
  <xsl:call-template name="make-label-text">
    <!--<xsl:with-param name="auto" select="$auto-number-fn"/>-->
    <xsl:with-param name="auto" select="true()"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>[</xsl:text>
      <xsl:number level="any" count="fn[not(parent::fn-group)]"
        from="article | sub-article | response"/>
      <xsl:text>]</xsl:text>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="table-wrap//fn" mode="label-text" priority="2">
  <xsl:param name="warning" select="false()"/>
  <xsl:variable name="empty-xrefs"
    select="key('xref-by-rid',@id)[not(normalize-space())]"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="boolean($empty-xrefs)"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>[</xsl:text>
      <xsl:number level="any" count="fn" from="table-wrap" format="i"/>
      <xsl:text>]</xsl:text>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<xsl:template match="fn-group/fn | author-notes/fn"
              mode="label-text">
  <!-- this template does not apply to footnotes inside
       table-wrap -->
  <xsl:param name="warning" select="true()"/>
  <!-- pass $warning in as false() if a warning string is not wanted
       (for example, if generating autonumbered labels) -->
  <xsl:variable name="empty-xrefs"
    select="key('xref-by-rid',@id)[not(normalize-space())]"/>
  <!-- auto-number this fn if it has any empty xrefs, unless we're
       in a table-wrap-foot -->
  <!--<xsl:variable name="auto-number-fn" select="boolean($empty-xrefs)
    and not(label|@symbol)"/>-->
  <xsl:variable name="auto-number-fn" select="true()"/>
  
  <xsl:variable name="fn-number">
      <xsl:number level="any" count="fn[not(ancestor::front)]"
      from="article | sub-article | response"/>
  </xsl:variable>

  <xsl:variable name="number-format">
    <xsl:choose>
      <xsl:when test="parent::author-notes">a</xsl:when>
      <xsl:when test="ancestor::boxed-text | ancestor::bio">i</xsl:when>
      <xsl:otherwise>1</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-number-fn"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <fo:basic-link internal-destination="xr{$fn-number}" id="fn{$fn-number}" xsl:use-attribute-sets="link">
        <xsl:copy-of select="$fn-number"/>
      </fo:basic-link>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="sec" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-sec"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>Section </xsl:text>
      <xsl:number level="multiple" from="article" format="1.1."/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="ref" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-ref"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:number level="any"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="statement" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-statement"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>Statement </xsl:text>
      <xsl:number level="any"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="supplementary-material" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-supplementary"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>Supplementary Material </xsl:text>
      <xsl:number level="any" format="A"
        count="supplementary-material[not(ancestor::front)]"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="table-wrap" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="auto" select="$auto-label-table-wrap"/>
    <xsl:with-param name="warning" select="$warning"/>
    <xsl:with-param name="auto-text">
      <xsl:text>Table </xsl:text>
      <xsl:number level="any" format="I"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template match="def-item" mode="label-text">
  <xsl:call-template name="item-mark"/>
  <xsl:text> </xsl:text>
</xsl:template>


<xsl:template match="list/list-item" mode="label-text">
  <xsl:variable name="given-label">
    <xsl:apply-templates select="label" mode="label-text"/>
  </xsl:variable>
  <xsl:copy-of select="$given-label"/>
  <xsl:if test="not(string($given-label))">
    <!-- a marker is generated only if the item has no
         label given -->
    <xsl:call-template name="item-mark"/>
  </xsl:if>
</xsl:template>


<xsl:template match="*" mode="label-text">
  <xsl:param name="warning" select="true()"/>
  <!-- pass $warning in as false() if a warning string is not wanted
       (for example, if generating autonumbered labels) -->
  <xsl:call-template name="make-label-text">
    <xsl:with-param name="warning" select="$warning"/>
  </xsl:call-template>
</xsl:template>


<xsl:template match="label" mode="label-text">
  <xsl:apply-templates/>
</xsl:template>


<!-- ============================================================= -->
<!-- MathML handling                                               -->
<!-- ============================================================= -->


<xsl:template match="mml:math">
  <xsl:choose>
    <xsl:when test="$mathml-support">
      <fo:instream-foreign-object>
        <xsl:copy>
          <xsl:copy-of select="@*"/>
          <xsl:apply-templates/>
        </xsl:copy>
      </fo:instream-foreign-object>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<xsl:template match="mml:*">
  <xsl:choose>
    <xsl:when test="$mathml-support">
  <xsl:copy>
    <xsl:copy-of select="@*"/>
    <xsl:apply-templates/>
  </xsl:copy>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!-- ============================================================= -->
<!-- Writing a name                                                -->
<!-- ============================================================= -->
<!-- Called when displaying structured names in metadata  -->

<xsl:template name="write-name" match="name">
  <xsl:apply-templates select="prefix" mode="inline-name"/>
  <xsl:apply-templates select="surname[../@name-style='eastern']" mode="inline-name"/>
  <xsl:apply-templates select="given-names" mode="inline-name"/>
  <xsl:apply-templates select="surname[not(../@name-style='eastern')]" mode="inline-name"/>
  <xsl:apply-templates select="suffix" mode="inline-name"/>
</xsl:template>


<xsl:template match="prefix" mode="inline-name">
  <xsl:apply-templates/>
  <xsl:if test="../surname | ../given-names | ../suffix">
    <xsl:text> </xsl:text>
  </xsl:if>
</xsl:template>


<xsl:template match="given-names" mode="inline-name">
  <xsl:apply-templates/>
  <xsl:if test="../surname[not(../@name-style='eastern')] | ../suffix">
    <xsl:text> </xsl:text>
  </xsl:if>
</xsl:template>


<xsl:template match="contrib/name/surname" mode="inline-name">
  <xsl:apply-templates/>
  <xsl:if test="../given-names[../@name-style='eastern'] | ../suffix">
    <xsl:text> </xsl:text>
  </xsl:if>
</xsl:template>


<xsl:template match="surname" mode="inline-name">
  <xsl:apply-templates/>
  <xsl:if test="../given-names[../@name-style='eastern'] | ../suffix">
    <xsl:text> </xsl:text>
  </xsl:if>
</xsl:template>


<xsl:template match="suffix" mode="inline-name">
  <xsl:apply-templates/>
</xsl:template>


<!-- string-name elements are written as is -->

<xsl:template match="string-name">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="string-name/*">
  <xsl:apply-templates/>
</xsl:template>


<!-- ============================================================= -->
<!-- UTILITY TEMPLATES                                             -->
<!-- ============================================================= -->


<xsl:template name="make-label-text">
  <xsl:param name="auto" select="false()"/>
  <xsl:param name="warning" select="false()"/>
  <xsl:param name="auto-text"/>

  <xsl:choose>
    <xsl:when test="$auto">
      <fo:inline xsl:use-attribute-sets="generated">
        <xsl:copy-of select="$auto-text"/>
      </fo:inline>
    </xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates mode="label-text" select="label | @symbol"/>
      <xsl:if test="$warning and not(label|@symbol)">
        <fo:inline xsl:use-attribute-sets="warning">
          <xsl:text>{ label</xsl:text>
          <xsl:if test="self::fn"> (or @symbol)</xsl:if>
          <xsl:text> needed for </xsl:text>
          <xsl:value-of select="local-name()"/>
          <xsl:for-each select="@id">
            <xsl:text>[@id='</xsl:text>
            <xsl:value-of select="."/>
            <xsl:text>']</xsl:text>
          </xsl:for-each>
          <xsl:text> }</xsl:text>
        </fo:inline>
      </xsl:if>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<xsl:template name="make-external-link">
  <xsl:param name="href">
	<xsl:choose>
		<xsl:when test="@xlink:href">
			<xsl:value-of select="@xlink:href"/>
		</xsl:when>
		<xsl:otherwise>
			<xsl:apply-templates/>
		</xsl:otherwise>
	</xsl:choose>
  </xsl:param>
  <xsl:param name="contents">
    <xsl:choose>
      <xsl:when test="normalize-space()">
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="@xlink:href"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:param>

	  <fo:basic-link external-destination="{$href}"
	    show-destination="new" xsl:use-attribute-sets="link">
	    <xsl:copy-of select="$contents"/>
	  </fo:basic-link>
</xsl:template>

<xsl:template name="make-internal-link">
  <xsl:param name="href" select="@href" >
  </xsl:param>
  <xsl:param name="id" select="@id"/>
  <xsl:param name="contents">
    <xsl:choose>
      <xsl:when test="normalize-space()">
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="@xlink:href"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:param> 
	  <fo:basic-link id="{$id}" internal-destination="{normalize-space($href)}"
	    show-destination="new" xsl:use-attribute-sets="link">
	    <xsl:copy-of select="$contents"/>
	  </fo:basic-link>
</xsl:template>

<xsl:template name="make-external-link-no-attribute-set">
  <xsl:param name="href">
   <xsl:choose>
      <xsl:when test="normalize-space()">
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
	 <xsl:value-of select="@contents"/>
      </xsl:otherwise>
   </xsl:choose>
  </xsl:param>
  <xsl:param name="contents">
    <xsl:choose>
      <xsl:when test="normalize-space()">
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="@xlink:href"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:param> 
	  <fo:basic-link external-destination="{normalize-space($href)}"
	    show-destination="new">
	    <xsl:copy-of select="$contents"/>
	  </fo:basic-link>
</xsl:template>


<xsl:template name="resolve-href">
  <!-- prepends an @xlink:href value with the $base-dir
       parameter, if it is given, plus a '/' delimiter:
       for locating graphics -->
  <xsl:for-each select="@xlink:href">
    <xsl:variable name="dir">
      <xsl:if test="$base-dir">
        <xsl:value-of select="$base-dir"/>
        <xsl:text>/</xsl:text>
      </xsl:if>
    </xsl:variable>
    <xsl:value-of select="$dir"/>
    <xsl:value-of select="."/>
  </xsl:for-each>
</xsl:template>


<xsl:template name="set-float">
  <!-- A float may be prohibited by passing $allow-float as false() -->
  <xsl:param name="allow-float" select="true()"/>
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:variable name="please-float"
    select="$allow-float and
            not(@position != 'float') and
            not(ancestor::*[@position][@position='float'])"/>
  <!-- assuming $allow-float is true(), the test respects 
         @position='float' as the default, and sets float to 'before' 
         but *only* if no ancestors with @position have a value of
         'float' -->
  <xsl:choose>
    <xsl:when test="$please-float">
      <fo:float xsl:use-attribute-sets="float">
        <xsl:copy-of select="$contents"/>
      </fo:float>
    </xsl:when>
    <xsl:otherwise>
      <xsl:copy-of select="$contents"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<xsl:template name="metadata-entry-cell">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:call-template name="make-metadata-cell">
    <xsl:with-param name="contents">
      <xsl:copy-of select="$contents"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template name="metadata-labeled-entry-cell">
  <xsl:param name="label"/>
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:call-template name="metadata-entry-cell">
    <xsl:with-param name="contents">
        <xsl:if test="normalize-space($label)">
          <fo:inline xsl:use-attribute-sets="metadata-label">
            <xsl:copy-of select="$label"/>
            <xsl:text>: </xsl:text>
          </fo:inline>
        </xsl:if>
      
      <xsl:choose>
        <xsl:when test="$label = 'DOI'">
          <fo:basic-link external-destination="url('http://dx.doi.org/{$contents}')" xsl:use-attribute-sets="link">
            <xsl:copy-of select="$contents"/>
          </fo:basic-link>
        </xsl:when>
        <xsl:otherwise>
          <xsl:copy-of select="$contents"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>

<xsl:template name="colon-separated-entry">
  <xsl:param name="label"/>
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
      <xsl:if test="normalize-space($label)">
        <fo:block xsl:use-attribute-sets="journal-metadata" text-align="right">
          <xsl:copy-of select="$label"/>
          <xsl:text>: </xsl:text>
          <xsl:copy-of select="$contents"/>
        </fo:block>
      </xsl:if>
</xsl:template>


<xsl:template name="metadata-area-cell">
  <xsl:param name="label"/>
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:call-template name="make-metadata-cell">
    <xsl:with-param name="contents">
      <xsl:if test="normalize-space($label)">
        <fo:block xsl:use-attribute-sets="metadata-label">
          <xsl:copy-of select="$label"/>
        </fo:block>
      </xsl:if>
      <fo:block start-indent="3em">
        <xsl:copy-of select="$contents"/>
      </fo:block>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template name="metadata-block">
  <xsl:param name="label"/>
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:block xsl:use-attribute-sets="metadata-line">
    <xsl:if test="normalize-space($label)">
      <fo:block xsl:use-attribute-sets="metadata-label">
        <xsl:copy-of select="$label"/>
      </fo:block>
    </xsl:if>
    <fo:block margin-left="3em">
      <xsl:copy-of select="$contents"/>
    </fo:block>
  </fo:block>

</xsl:template>


<xsl:template name="metadata-line">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:block xsl:use-attribute-sets="metadata-line">
    <xsl:copy-of select="$contents"/>
  </fo:block>
</xsl:template>


<xsl:template name="metadata-labeled-line">
  <xsl:param name="label"/>
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <xsl:call-template name="metadata-line">
    <xsl:with-param name="contents">
      <xsl:if test="normalize-space($label)">
        <fo:inline xsl:use-attribute-sets="metadata-label">
          <xsl:copy-of select="$label"/>
          <xsl:text>: </xsl:text>
        </fo:inline>
      </xsl:if>
      <xsl:copy-of select="$contents"/>
    </xsl:with-param>
  </xsl:call-template>
</xsl:template>


<xsl:template name="make-metadata-cell">
  <xsl:param name="contents">
    <xsl:apply-templates/>
  </xsl:param>
  <fo:table-row>
    <fo:table-cell padding-top="2pt" padding-left="0.1in" border-style="solid"
      border-width="1pt">
      <fo:block xsl:use-attribute-sets="metadata-line">
        <xsl:copy-of select="$contents"/>
      </fo:block>
    </fo:table-cell>
  </fo:table-row>
</xsl:template>


<xsl:template name="append-pub-type">
  <!-- adds a value mapped for @pub-type, enclosed in parenthesis,
       to a string -->
  <xsl:for-each select="@pub-type">
    <xsl:text> (</xsl:text>
    <fo:inline xsl:use-attribute-sets="data">
      <xsl:choose>
        <xsl:when test=".='epub'">electronic</xsl:when>
        <xsl:when test=".='ppub'">print</xsl:when>
        <xsl:when test=".='epub-ppub'">print and electronic</xsl:when>
        <xsl:when test=".='epreprint'">electronic preprint</xsl:when>
        <xsl:when test=".='ppreprint'">print preprint</xsl:when>
        <xsl:when test=".='ecorrected'">corrected, electronic</xsl:when>
        <xsl:when test=".='pcorrected'">corrected, print</xsl:when>
        <xsl:when test=".='eretracted'">retracted, electronic</xsl:when>
        <xsl:when test=".='pretracted'">retracted, print</xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="."/>
        </xsl:otherwise>
      </xsl:choose>
    </fo:inline>
    <xsl:text>)</xsl:text>
  </xsl:for-each>
</xsl:template>


<!-- Template "item-mark" generates a bullet or number for a 
     list-item or to appear with a def-list/term -->

<xsl:template name="item-mark">
  <!-- the context is a list/list-item or a def-list/def-item -->
  <xsl:if test="../@list-type='bullet' or parent::list[not(@list-type)]">
    <xsl:call-template name="get-bullet"/>
    <xsl:if test="../@prefix-word">
      <xsl:text> </xsl:text>
    </xsl:if>
  </xsl:if>
  <xsl:value-of select="../@prefix-word"/>
  <xsl:if test="../@list-type[not(.='simple' or .='bullet')]">
    <!-- for an item with an explicit list type other than 'simple'
      or 'bullet', we generate a number -->
    <xsl:variable name="number-format">
      <xsl:call-template name="list-number-format"/>
    </xsl:variable>
    <xsl:variable name="number">
      <xsl:call-template name="list-item-number"/>
    </xsl:variable>
    <xsl:text> </xsl:text>
    <xsl:number value="$number" format="{$number-format}"/>
  </xsl:if>
</xsl:template>


<!-- Template 'get-bullet' assigns a bullet character based on the
     depth of the list containing the item -->

<xsl:template name="get-bullet">
  <xsl:variable name="list-depth"
    select="count(ancestor::*
            [@list-type='bullet' or self::list[not(@list-type)]])"/>
  <xsl:choose>
    <xsl:when test="$list-depth mod 5 = 1">
      <!-- bullet -->
      <xsl:text>&#x2022;</xsl:text>
    </xsl:when>
    <xsl:when test="$list-depth mod 5 = 2">
      <!-- disc -->
      <xsl:text>&#x25E6;</xsl:text>
    </xsl:when>
    <xsl:when test="$list-depth mod 5 = 3">
      <!-- square -->
      <xsl:text>&#x25AA;</xsl:text>
    </xsl:when>
    <xsl:when test="$list-depth mod 5 = 4">
      <!-- white square -->
      <xsl:text>&#x25AB;</xsl:text>
    </xsl:when>
    <xsl:when test="$list-depth mod 5 = 0">
      <!-- dash -->
      <xsl:text>&#x2013;</xsl:text>
    </xsl:when>
  </xsl:choose>
</xsl:template>


<!-- Template 'list-number-format' designates a format to be used
     for numbering a list item, based on settings on its list parent
     and (sometimes) ancestors -->

<xsl:template name="list-number-format">
  <!-- the context is the item -->
  <xsl:choose>
    <xsl:when test="../@list-type='order'">
      <xsl:variable name="list-depth"
        select="count(ancestor::*[@list-type='order'])"/>
      <xsl:choose>
        <xsl:when test="$list-depth mod 6 = 1">1.</xsl:when>
        <xsl:when test="$list-depth mod 6 = 2">a.</xsl:when>
        <xsl:when test="$list-depth mod 6 = 3">1)</xsl:when>
        <xsl:when test="$list-depth mod 6 = 4">a)</xsl:when>
        <xsl:when test="$list-depth mod 6 = 5">i.</xsl:when>
        <xsl:when test="$list-depth mod 6 = 0">i)</xsl:when>
      </xsl:choose>
    </xsl:when>
    <xsl:when test="../@list-type='alpha-lower'">a.</xsl:when>
    <xsl:when test="../@list-type='alpha-upper'">A.</xsl:when>
    <xsl:when test="../@list-type='roman-lower'">i.</xsl:when>
    <xsl:when test="../@list-type='roman-upper'">I.</xsl:when>
    <!-- the otherwise case will catch values of @list-type
         not recognized by the stylesheet -->
    <xsl:otherwise>1.</xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!-- Template 'list-item-number' determines a number for a list
     item, accounting for @continued-from on its parent -->

<xsl:template name="list-item-number">
  <xsl:param name="here" select="parent::list|parent::def-list"/>
  <xsl:param name="item-number">
    <!-- the first time through, this is the number of the item -->
    <xsl:number/>
  </xsl:param>
  <xsl:choose>
    <!-- if this list is not continued from another, the item
         number is returned -->
    <xsl:when
      test="not(key('element-by-id',$here/@continued-from)
                        [self::list|self::def-list])">
      <xsl:value-of select="$item-number"/>
    </xsl:when>
    <xsl:otherwise>
      <!-- otherwise, we call this template recursively,
           adding in the count of the continued list -->
      <xsl:call-template name="list-item-number">
        <xsl:with-param name="here"
          select="key('element-by-id',$here/@continued-from)"/>
        <xsl:with-param name="item-number"
          select="$item-number + count($here/list-item|$here/def-item)"/>
      </xsl:call-template>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!-- Template "process-style" maps arbitrary CSS into FO, with
     some provision for mapping table-related values  -->
<!-- Modified from AntennaHouse code -->

<xsl:template name="process-style">
  <xsl:param name="style"/>
  <!-- e.g., style="text-align: center; color: red"
  converted to text-align="center" color="red" -->
  <xsl:variable name="okay-properties"
    select="' color; background-color; font-size; font-weight;
              font-style; font-family; text-decoration; text-align'"/>
  <xsl:variable name="name"
    select="normalize-space(substring-before($style, ':'))"/>
  <xsl:if test="$name">
    <xsl:variable name="value-and-rest"
      select="normalize-space(substring-after($style, ':'))"/>
    <xsl:variable name="value">
      <xsl:choose>
        <xsl:when test="contains($value-and-rest, ';')">
          <xsl:value-of
            select="normalize-space(substring-before(
                      $value-and-rest, ';'))"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$value-and-rest"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="$name = 'width' and (self::col or self::colgroup)">
        <xsl:attribute name="column-width">
          <xsl:value-of select="$value"/>
        </xsl:attribute>
      </xsl:when>
      <xsl:when
        test="$name = 'vertical-align' and (
                               self::table or self::caption or
                               self::thead or self::tfoot or
                               self::tbody or self::colgroup or
                               self::col or self::tr or
                               self::th or self::td)">
        <xsl:choose>
          <xsl:when test="$value = 'top'">
            <xsl:attribute name="display-align">before</xsl:attribute>
          </xsl:when>
          <xsl:when test="$value = 'bottom'">
            <xsl:attribute name="display-align">after</xsl:attribute>
          </xsl:when>
          <xsl:when test="$value = 'middle'">
            <xsl:attribute name="display-align">center</xsl:attribute>
          </xsl:when>
          <xsl:otherwise>
            <xsl:attribute name="display-align">auto</xsl:attribute>
            <xsl:attribute name="relative-align">baseline</xsl:attribute>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <xsl:if test="contains($okay-properties,concat(' ',$name,';'))">
          <xsl:attribute name="{$name}">
            <xsl:value-of select="$value"/>
          </xsl:attribute>
        </xsl:if>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:if>
  <xsl:variable name="rest"
    select="normalize-space(substring-after($style, ';'))"/>
  <xsl:if test="$rest">
    <xsl:call-template name="process-style">
      <xsl:with-param name="style" select="$rest"/>
    </xsl:call-template>
  </xsl:if>
</xsl:template>


<!-- ============================================================= -->
<!-- Stylesheeet diagnostics                                       -->
<!-- ============================================================= -->
<!-- For generating warnings to be reported due to processing
     anomalies. -->

<xsl:template name="run-diagnostics">
  <xsl:variable name="diagnostics">
    <xsl:call-template name="process-warnings"/>
  </xsl:variable>
  <xsl:if test="normalize-space($diagnostics)">
    <fo:page-sequence master-reference="diagnostics-sequence">
      <fo:static-content flow-name="recto-header">
        <fo:block xsl:use-attribute-sets="page-header">
          <xsl:call-template name="make-page-header">
            <xsl:with-param name="center-cell">
              <fo:block text-align="center">Process Warnings</fo:block>
            </xsl:with-param>
          </xsl:call-template>
        </fo:block>
      </fo:static-content>
      <fo:static-content flow-name="verso-header">
        <fo:block xsl:use-attribute-sets="page-header">
          <xsl:call-template name="make-page-header">
            <xsl:with-param name="center-cell">
              <fo:block text-align="center">Process Warnings</fo:block>
            </xsl:with-param>
          </xsl:call-template>
        </fo:block>
      </fo:static-content>
      <xsl:call-template name="define-footnote-separator"/>
      <fo:flow flow-name="body">
        <fo:block line-stacking-strategy="font-height"
          line-height-shift-adjustment="disregard-shifts">

          <!-- set the article opener, body, and backmatter -->
          <xsl:copy-of select="$diagnostics"/>
        </fo:block>
      </fo:flow>
    </fo:page-sequence>
  </xsl:if>
</xsl:template>


<xsl:template name="process-warnings">
  <!-- returns an RTF containing all the warnings -->
  <xsl:variable name="xref-warnings">
    <xsl:for-each select="//xref[not(normalize-space())]">
      <!-- we only check an xref that is first to reference its
           target -->
      <xsl:if test="generate-id(.) =
                    generate-id(key('xref-by-rid',@rid)[1])">
        <xsl:variable name="target-label">
          <xsl:apply-templates select="key('element-by-id',@rid)"
            mode="label-text">
            <xsl:with-param name="warning" select="false()"/>
          </xsl:apply-templates>
        </xsl:variable>
        <xsl:if test="not(normalize-space($target-label))">
          <!-- if we failed to get a label with no warning
               we ask again to get the warning -->
          <fo:list-item xsl:use-attribute-sets="list-item">
            <fo:list-item-label end-indent="label-end()">
              <fo:block xsl:use-attribute-sets="list-item-label">
                <xsl:text>&#x2022;</xsl:text>
              </fo:block>
            </fo:list-item-label>
            <fo:list-item-body start-indent="body-start()">
              <fo:block>
                <xsl:apply-templates select="key('element-by-id',@rid)"
                  mode="label-text">
                  <xsl:with-param name="warning" select="true()"/>
                </xsl:apply-templates>
              </fo:block>
            </fo:list-item-body>
          </fo:list-item>
        </xsl:if>
      </xsl:if>
    </xsl:for-each>
  </xsl:variable>

  <xsl:if test="normalize-space($xref-warnings)">
    <xsl:call-template name="section-title">
      <xsl:with-param name="contents">
        <xsl:text>Elements cross-referenced without labels</xsl:text>
      </xsl:with-param>
    </xsl:call-template>

    <fo:block xsl:use-attribute-sets="paragraph">
      <xsl:text>Either the element should be provided a label, </xsl:text>
      <xsl:text>or their cross-reference(s) should have </xsl:text>
      <xsl:text>literal text content.</xsl:text>
    </fo:block>
    <fo:list-block provisional-distance-between-starts="12pt"
      provisional-label-separation="6pt">
      <xsl:copy-of select="$xref-warnings"/>
    </fo:list-block>
  </xsl:if>
</xsl:template>


<!-- ============================================================= -->
<!-- Date formatting                                               -->
<!-- ============================================================= -->
<!-- Maps a structured date element to a string -->

<xsl:template name="format-date">
  <!-- formats date in DD Month YYYY format -->
  <!-- context must be 'date', with content model:
       (((day?, month?) | season)?, year) -->
  <xsl:for-each select="day|month|season">
    <xsl:apply-templates select="." mode="map"/>
    <xsl:text> </xsl:text>
  </xsl:for-each>
  <xsl:apply-templates select="year" mode="map"/>
</xsl:template>


<xsl:template match="day | season | year" mode="map">
  <xsl:apply-templates/>
</xsl:template>


<xsl:template match="month" mode="map">
  <!-- maps numeric values to English months -->
  <xsl:choose>
    <xsl:when test="number() = 1">January</xsl:when>
    <xsl:when test="number() = 2">February</xsl:when>
    <xsl:when test="number() = 3">March</xsl:when>
    <xsl:when test="number() = 4">April</xsl:when>
    <xsl:when test="number() = 5">May</xsl:when>
    <xsl:when test="number() = 6">June</xsl:when>
    <xsl:when test="number() = 7">July</xsl:when>
    <xsl:when test="number() = 8">August</xsl:when>
    <xsl:when test="number() = 9">September</xsl:when>
    <xsl:when test="number() = 10">October</xsl:when>
    <xsl:when test="number() = 11">November</xsl:when>
    <xsl:when test="number() = 12">December</xsl:when>
    <xsl:otherwise>
      <xsl:apply-templates/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>


<!-- ============================================================= -->
<!-- ID assignment                                                 -->
<!-- ============================================================= -->
<!-- An id can be derived for any element. If an @id is given,
     it is presumed unique and copied. If not, one is generated.   -->
  
<xsl:template name="assign-id">
  <xsl:variable name="id">
    <xsl:apply-templates select="." mode="id"/>
  </xsl:variable>
  <xsl:attribute name="id">
    <xsl:value-of select="$id"/>
  </xsl:attribute>
</xsl:template>


<xsl:template match="*" mode="id">
  <xsl:value-of select="@id"/>
  <xsl:if test="not(@id)">
    <xsl:value-of select="generate-id(.)"/>
  </xsl:if>
</xsl:template>


<xsl:template match="article | sub-article | response" mode="id">
  <xsl:value-of select="@id"/>
  <xsl:if test="not(@id)">
    <xsl:value-of select="local-name()"/>
    <xsl:number from="article" level="multiple"
      count="article | sub-article | response" format="1-1"/>
  </xsl:if>
</xsl:template>


<!-- ============================================================= -->
<!-- END OF STYLESHEET                                             -->
<!-- ============================================================= -->

</xsl:stylesheet>
