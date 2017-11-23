<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:nlm="http://www.ncbi.nlm.gov/xslt/util">
  
  <!-- ============================================================= -->
  <!--  MODULE:    Journal Publishing 3.0 APA-like Citation          -->
  <!--             Preprocessor                                      -->
  <!--  VERSION:   1.0                                               -->
  <!--  DATE:      December 2008                                     -->
  <!--                                                               -->
  <!-- ============================================================= -->
  
  <!-- ============================================================= -->
  <!--  SYSTEM:    NCBI Archiving and Interchange Journal Articles   -->
  <!--                                                               -->
  <!--  PURPOSE:   Punctuate and format unpunctuated citation        -->
  <!--             elements according to APA formatting              -->
  <!--             rules, to the extent this can reasonably be       -->
  <!--             specified.                                        -->
  <!--                                                               -->
  <!--             Apart from its handling of citations, this is     -->
  <!--             an identity transform.                            -->
  <!--                                                               -->
  <!--  CONTAINS:  Documentation:                                    -->
  <!--               D1) Change history                              -->
  <!--               D2) Structure of this transform                 -->
  <!--               D3) Constraints on the transform                -->
  <!--                                                               -->
  <!--  PROCESSOR DEPENDENCIES:                                      -->
  <!--             None: standard XSLT 2.0                           -->
  <!--             Tested using Saxon 9.1.0.3                        -->
  <!--                                                               -->
  <!--  COMPONENTS REQUIRED:                                         -->
  <!--             1) This stylesheet                                -->
  <!--                                                               -->
  <!--  INPUT:     An XML document valid with the                    -->
  <!--             Journal Publishing 3.0 DTD.                       -->
  <!--             (And note further assumptions below.)             -->
  <!--                                                               -->
  <!--  OUTPUT:    The same, except citation elements appear         -->
  <!--             punctuated and formatted.                         -->
  <!--             NOTE: 'nlm-citation' elements in the source data  -->
  <!--             are passed through unchanged; rendering these     -->
  <!--             into APA format is out of scope for this          -->
  <!--             transform.                                        -->
  <!--                                                               -->
  <!--  ORIGINAL CREATION DATE:                                      -->
  <!--             December 2008                                     -->
  <!--                                                               -->
  <!--  CREATED FOR:                                                 -->
  <!--             Digital Archive of Journal Articles               -->
  <!--             National Center for Biotechnology Information     -->
  <!--                (NCBI)                                         -->
  <!--             National Library of Medicine (NLM)                -->
  <!--                                                               -->
  <!--  CREATED BY:                                                  -->
  <!--             Wendell Piez, Mulberry Technologies, Inc.         -->
  <!--                                                               -->
  <!-- ============================================================= -->
  
  <!-- ============================================================= -->
  <!--  D1) STYLESHEET VERSION / CHANGE HISTORY                      -->
  <!-- =============================================================
    
    1.  v. 1.00                                         2008-12-10
    
    This is the inital preprocessing transform for formatting
    structured citations.
  -->
  <!-- ============================================================= -->
  
  <!-- ============================================================= -->
  <!--  D2) STRUCTURE OF THIS TRANSFORM                              -->
  <!-- ============================================================= -->
  
  <!--  Citation elements include 'element-citation',
    'mixed-citation' and its relatives, 'product',
    'related-article' and 'related-object'.
    
    Note that 'nlm-citation' is not handled by this transform.
    
    The purpose of this transform is to provide formatting,
    including punctuation, for unpunctuated citations. This
    includes 'element-citation' elements (which are permitted 
    only element content by the DTD) and other citation elements 
    when they are unpunctuated in the source.
    
    The transform consists of the following parts:
    
    1) Default handling for all elements: the identity template
    
    2) Templates matching citation elements: passing them through
    when already punctuated, or mapping them to appropriate
    handling based on @publication-type when not punctuated
    
    3) Named templates for generating contents for four 
    recognized citation types:
    'fallback-citation-content' for unrecognized citation types
    'journal-citation-content' for journals and conference
    papers
    'book-citation-content' for books and dissertations
    'book-chapter-citation-content' for chapters and articles
    published in books
    
    4) Named utility templates and generic speciality modes. These
    templates are called in service of more than one citation
    type.
    
    5) Templates in mode 'format': these templates do not provide
    punctuation, but allow for casting of elements into
    equivalents with explicit formatting. They are used even
    when processing citations that are already punctuated.
    
    6) Specialty modes for particular citation types. Modes include
    'article-item', 'book-item' and 'book-chapter-item'. These
    provide for specialized handling of elements based on
    citation type.
    
    7) Function 'nlm:fetch-comment()', used to acquire comment
    elements punctuated with brackets with other elements,
    so that they may be to be punctuated together.
  -->
  
  <!-- ============================================================= -->
  <!--  D3) CONSTRAINTS ON AND LIMITATIONS OF THE TRANSFORM          -->
  <!-- ============================================================= -->
  
  <!-- This stylesheet punctuates and formats citations that were
    tagged in according to an APA-like citation style, but
    without spacing or punctuation, in preparation for formatting
    them using the Preview stylesheets (distributed in the same
    package). We say "APA-like" in recognition of the many
    variations on APA style used by publishers and authors.
    
    Input must be valid Journal Publishing 3.0 XML.
    
    Element content of element-citation and punctuated
    mixed-citation elements (as well as the related elements
    'product', 'related-article' and 'related-object'
    when they are unpunctuated) must appear in the order expected 
    by APA format. To an extent, this transform will work even 
    if elements appear out of order, but no warrant is made that 
    it will.
    
    This stylesheet will not repunctuate citations that are
    already punctuated in input; it restricts itself to providing
    formatting for citations not already formatted.
    
    This stylesheet does not handle nlm-citation elements, copying
    them over as they appear in the source.
    
    Output is Journal Publishing 3.0 with the following additional
    constraints:
    
    1. element-citation elements do not appear.
    
    2. citation elements in the result (including mixed-citation,
    product, related-article, related-object, whether or not 
    they are punctuated in the source) conform to this content
    model:
    
    (#PCDATA | bold | italic | monospace | overline | roman |
    sans-serif | sc | strike | underline | inline-graphic |
    label | email | ext-link | uri | sub | sup | styled-content)*
    
    3. Other elements allowed in citations in the tag set, which 
    should not appear in the result, include the following:
    
    abbrev, alternatives, annotation, article-title,
    chapter-title, chem-struct, collab, comment, conf-date,
    conf-loc, conf-name, conf-sponsor, date, date-in-citation,
    day, edition, elocation-id, etal, fpage, gov,
    inline-formula, institution, isbn, issn, issue, issue-id,
    issue-part, issue-title, lpage, milestone-end,
    milestone-start, month, name, named-content, object-id,
    page-range, part-title, patent, person-group, private-char,
    pub-id, publisher-loc, publisher-name, role, season,
    series, size, source, std, string-name, supplement,
    trans-source, trans-title, volume, volume-id, volume-
    series, year.
    
    LIMITATIONS IN FORMATTING OF APA-LIKE CITATIONS
    
    Results of this stylesheet are "APA-like", in that it creates 
    renditions of the commonest citation types from Journal
    Publishing source data in a format that generally conforms 
    to APA guidelines, without warrant that it covers uncommon 
    forms of citations or special uses or edge cases of common ones.
    
    The heuristics used to sort between the various elements
    inside element-citation are sensitive to the ordering of
    those elements, so placing the elements in the correct order
    is necessary for the correct functioning of the formatting
    logic.
    
    When this logic is insufficient to format a particular
    citation correctly, a user or publisher has two options:
    
    1. Use mixed-citation instead of element-citation, and
    present the correct punctuation in the XML. This will be an
    easy solution for many projects, where the source data is
    already punctuated. (Markup inside mixed-citation can  still
    be used to identify the parts of the citation.)
    
    2. This stylesheet can be extended with new formatting logic
    to handle citation types and/or elements that are not already
    handled.
    
    SCOPE AND OPERATION OF THIS STYLESHEET
    
    The three main citation types covered here are "journal", for
    journal articles, "book" for monographs, and "book-chapter",
    for articles or chapters cited from within books.
    
    In addition, two secondary citation types are supported,
    "conference" for unpublished conference papers (formatted
    mostly like journal articles), and "dissertation" for
    dissertations (formatted mostly like books).
    
    Note that these named types may correspond only roughly to
    the best type for any given citation. For example, volumes of
    conference proceedings should be formatted as books, while
    dissertations cited from Dissertation Abstracts International
    should be cited as journal articles. Users may have to
    experiment for best results.
    
    In accordance with the APA Publication Manual, the general
    pattern followed by all these types is the same:
    
    1. An identifying string for the citation appears. When
    available, this should be a list of authors of the work. When
    no authors are given, it should be the primary title of the
    work.
    
    Authors of a work are distinguished as any elements
    representing persons that appear before any elements that do
    not represent persons.
    
    For these purposes, the primary title of a citation of type
    "journal" is taken to be the first 'article-title' or 'trans-
    title' given in the citation. The primary title of a book is
    the first 'source' or 'trans-title' given. The primary title
    of a book chapter or article is the first 'article-title',
    'chapter-title' or 'trans-title' given.
    
    2. The date of the work, given either by a 'date' element
    (with structured content), or when no 'date' is given, by
    'year', 'month', 'day', and 'season' elements (the first of
    each that are available), or by 'date-in-citation' when none
    of these are available.
    
    Note that 'date-in-citation' may include non-date strings
    that serve as dates for these purposes, such as "no date" or
    "in press".
    
    3. The primary title of the work, if it has not already
    appeared.
    
    4. Any subsequent information particular to the citation
    type, such as the journal, volume and issue, publisher, page
    numbers, etc.
  -->
  <!-- ============================================================= -->
  
  
  <!-- ============================================================= -->
  <!-- Top-level and generic handling                                -->
  <!-- ============================================================= -->
  
  <!-- In general, the document is copied as-is -->
  
  <xsl:template match="*">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>
  
  
  <!-- Note that nlm-citation elements in particular are copied
    as is, with no modification -->
  <xsl:template match="nlm-citation">
    <xsl:copy-of select="."/>
  </xsl:template>
  
  
  <!-- When they have non-whitespace content, mixed-citation and 
    family members are taken to be formatted, and processed 
    in 'format' mode, which maps inline markup but does not
    punctuate. -->
  <xsl:template
    match="mixed-citation[text()[normalize-space()]] |
    product[text()[normalize-space()]] |
    related-article[text()[normalize-space()]] |
    related-object[text()[normalize-space()]]">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates mode="format"/>
    </xsl:copy>
  </xsl:template>
  
  
  <!-- If it fails to match the foregoing template, mixed-citation
    is treated like element-citation -->
  <xsl:template
    match="element-citation | mixed-citation">
    <!-- forgive the xsl:choose; exploding this into eight templates 
      (or more) would be too much of a good thing, and this is 
      easy to maintain -->
    <mixed-citation>
      <xsl:copy-of select="@*"/>
      <xsl:choose>
        <xsl:when test="@publication-type='journal'
          or @publication-type='conference'">
          <xsl:call-template name="journal-citation-content"/>
        </xsl:when>
        <xsl:when test="@publication-type='book'
          or @publication-type='dissertation'">
          <xsl:call-template name="book-citation-content"/>
        </xsl:when>
        <xsl:when test="@publication-type='bookchapter'">
          <xsl:call-template name="book-chapter-citation-content"/>
        </xsl:when>
        <xsl:when test="@publication-type='book-chapter'">
          <xsl:call-template name="book-chapter-citation-content"/>
        </xsl:when>
        <xsl:when test="@publication-type='articlereprint'">
          <xsl:call-template name="journal-citation-content-reprint"/>
        </xsl:when>
        <xsl:when test="@publication-type='letter'">
          <xsl:call-template name="letter-citation-content"/>
        </xsl:when>
        <xsl:when test="@publication-type">
          <!-- fallback format is invoked when @publication-type
            is present but unrecognized -->
          <xsl:call-template name="fallback-citation-content"/>
        </xsl:when>
        <xsl:otherwise>
          <!-- when @publication-type is not even given, we assume
            this is a journal article citation -->
          <xsl:call-template name="journal-citation-content"/>
        </xsl:otherwise>
      </xsl:choose>
    </mixed-citation>
  </xsl:template>
  
  
  <!-- Similarly, unformatted related-article is assumed to be
    a journal citation -->
  <xsl:template match="related-article">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:call-template name="journal-citation-content"/>
    </xsl:copy>
  </xsl:template>
  
  
  <!-- And unformatted related-object or product is assumed to be
    a book -->
  <xsl:template match="related-object | product">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:call-template name="book-citation-content"/>
    </xsl:copy>
  </xsl:template>
  
  
  <!-- ============================================================= -->
  <!-- Publication type templates                                    -->
  <!-- ============================================================= -->
  
  <!-- Fallback template for citations not specifically matched
    by type -->
  <xsl:template name="fallback-citation-content">
    <xsl:call-template name="comma-sequence-sentence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:apply-templates select="*" mode="format"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  
  
  <!-- ============================================================= -->
  <!-- For publication type 'letter'              -->
  <!-- ============================================================= -->
  
  <xsl:template name="letter-citation-content">
    <!-- assigning interesting element children to variables -->
    <xsl:variable name="all-names"
      select="(person-group|name|collab|anonymous|etal|string-name)
      / (. | nlm:fetch-comment(.))"/>
    <!-- $all-authors are all the elements that might be authors -->
    <xsl:variable name="placed-names"
      select="$all-names[not(preceding-sibling::* intersect 
      (current()/* except $all-names))]"/>
    <!-- placed authors are all person-groups and all the elements
      that might be authors, except when they are preceded by 
      elements that can't be authors -->
    <xsl:variable name="date"
      select="date[1] | conf-date[1][not(date)] |
      (year[1]|month[1]|day[1]|season[1])
      [not(exists(date|conf-date))] |
      date-in-citation[1]
      [not(exists(date|conf-date|year|month|day|season))]"/>
    <!-- the date is either the first date element, or the first
      year, month, day and season elements when there is no 
      date element, or the first date-in-citation when none 
      of these are available -->
    <xsl:variable name="titles"
      select="(article-title | trans-title) /
      (. | nlm:fetch-comment(.))"/>
    <xsl:variable name="placed-title"
      select="($titles)[1][not($placed-names)] /
      (. | nlm:fetch-comment(.))"/>
    <xsl:variable name="conference" select="conf-name | conf-loc"/>
    
    <!-- now processing elements in chunks -->
    <xsl:call-template name="format-names">
      <xsl:with-param name="names"
        select="$placed-names except comment"/>
    </xsl:call-template>
    <!-- we have a placed title to do if there are no placed
      authors (skipping the comment with it as that will be 
      picked up subsequently) -->
    <xsl:apply-templates select="$placed-title except comment"
      mode="article-title"/>
    
    <xsl:apply-templates mode="article-title"
      select="$titles except ($placed-title | comment)"/>
    <xsl:call-template name="comma-sequence-sentence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:apply-templates mode="article-item"
          select="$conference"/>
      </xsl:with-param>
    </xsl:call-template>
    
    <xsl:variable name="dateformatted"><xsl:if test="boolean($date/day)"><xsl:value-of select="$date/day"/><xsl:text> </xsl:text></xsl:if><xsl:if test="boolean($date/month)"><xsl:value-of select="$date/month"/></xsl:if></xsl:variable>
    
    <xsl:call-template name="comma-sequence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:choose>
          <xsl:when test="$dateformatted != ''">
            <xsl:apply-templates mode="article-item"
              select="source, publisher-loc, issue, volume, $dateformatted, date/year, year, uri, pub-id" />
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates mode="article-item"
              select="source, publisher-loc, issue, volume, date/year, year, uri, pub-id" />
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
    <!--* except ($placed-names | $date |
      $titles | $conference)"/>-->
    
  </xsl:template>
  
  
  <!-- ============================================================= -->
  <!-- For publication types 'journal' and 'conference'              -->
  <!-- ============================================================= -->
  
  <xsl:template name="journal-citation-content">
    <!-- assigning interesting element children to variables -->
    <xsl:variable name="all-names"
      select="(person-group|name|collab|anonymous|etal|string-name)
      / (. | nlm:fetch-comment(.))"/>
    <!-- $all-authors are all the elements that might be authors -->
    <xsl:variable name="placed-names"
      select="$all-names[not(preceding-sibling::* intersect 
      (current()/* except $all-names))]"/>
    <!-- placed authors are all person-groups and all the elements
      that might be authors, except when they are preceded by 
      elements that can't be authors -->
    <xsl:variable name="date"
      select="date[1] | conf-date[1][not(date)] |
      (year[1]|month[1]|day[1]|season[1])
      [not(exists(date|conf-date))] |
      date-in-citation[1]
      [not(exists(date|conf-date|year|month|day|season))]"/>
    <!-- the date is either the first date element, or the first
      year, month, day and season elements when there is no 
      date element, or the first date-in-citation when none 
      of these are available -->
    <xsl:variable name="titles"
      select="(article-title | trans-title) /
      (. | nlm:fetch-comment(.))"/>
    <xsl:variable name="placed-title"
      select="($titles)[1][not($placed-names)] /
      (. | nlm:fetch-comment(.))"/>
    <xsl:variable name="conference" select="conf-name | conf-loc"/>
    
    <!-- now processing elements in chunks -->
    <xsl:call-template name="format-names">
      <xsl:with-param name="names"
        select="$placed-names except comment"/>
    </xsl:call-template>
    <!-- we have a placed title to do if there are no placed
      authors (skipping the comment with it as that will be 
      picked up subsequently) -->
    <xsl:apply-templates select="$placed-title except comment"
      mode="article-title"/>
    
    <xsl:apply-templates mode="article-title"
      select="$titles except ($placed-title | comment)"/>
    <xsl:call-template name="comma-sequence-sentence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:apply-templates mode="article-item"
          select="$conference"/>
      </xsl:with-param>
    </xsl:call-template>
    
    <xsl:variable name="dateformatted"><xsl:if test="boolean($date/day)"><xsl:value-of select="$date/day"/><xsl:text> </xsl:text></xsl:if><xsl:if test="boolean($date/month)"><xsl:value-of select="$date/month"/></xsl:if></xsl:variable>
    
    <xsl:call-template name="comma-sequence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:choose>
          <xsl:when test="$dateformatted != ''">
            <xsl:apply-templates mode="article-item"
              select="source, issue, volume, $dateformatted, date/year, year, uri, pub-id" />
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates mode="article-item"
              select="source, issue, volume, date/year, year, uri, pub-id" />
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
    <!--* except ($placed-names | $date |
      $titles | $conference)"/>-->
    
    <xsl:choose>
      <xsl:when test="boolean(fpage) and boolean(lpage)">, pp. <xsl:value-of select="fpage" /> - <xsl:value-of select="lpage" /></xsl:when>
      <xsl:when test="boolean(fpage) and boolean(lpage) = false()">, p. <xsl:value-of select="fpage" /></xsl:when>
    </xsl:choose>
    
  </xsl:template>
  
  <xsl:template name="journal-citation-content-reprint">
    <!-- assigning interesting element children to variables -->
    <xsl:variable name="all-names"
      select="(person-group|name|collab|anonymous|etal|string-name)
      / (. | nlm:fetch-comment(.))"/>
    <!-- $all-authors are all the elements that might be authors -->
    <xsl:variable name="placed-names"
      select="$all-names[not(preceding-sibling::* intersect 
      (current()/* except $all-names))]"/>
    <!-- placed authors are all person-groups and all the elements
      that might be authors, except when they are preceded by 
      elements that can't be authors -->
    <xsl:variable name="date"
      select="date[1] | conf-date[1][not(date)] |
      (year[1]|month[1]|day[1]|season[1])
      [not(exists(date|conf-date))] |
      date-in-citation[1]
      [not(exists(date|conf-date|year|month|day|season))]"/>
    <!-- the date is either the first date element, or the first
      year, month, day and season elements when there is no 
      date element, or the first date-in-citation when none 
      of these are available -->
    <xsl:variable name="titles"
      select="(article-title | trans-title) /
      (. | nlm:fetch-comment(.))"/>
    <xsl:variable name="placed-title"
      select="($titles)[1][not($placed-names)] /
      (. | nlm:fetch-comment(.))"/>
    <xsl:variable name="conference" select="conf-name | conf-loc"/>
    
    <!-- now processing elements in chunks -->
    <xsl:call-template name="format-names">
      <xsl:with-param name="names"
        select="$placed-names except comment"/>
    </xsl:call-template>
    <!-- we have a placed title to do if there are no placed
      authors (skipping the comment with it as that will be 
      picked up subsequently) -->
    <xsl:apply-templates select="$placed-title except comment"
      mode="article-title"/>
    
    <xsl:apply-templates mode="article-title"
      select="$titles except ($placed-title | comment)"/>
    <xsl:call-template name="comma-sequence-sentence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:apply-templates mode="article-item"
          select="$conference"/>
      </xsl:with-param>
    </xsl:call-template>
    
    <xsl:variable name="dateformatted"><xsl:if test="boolean($date/day)"><xsl:value-of select="$date/day"/><xsl:text> </xsl:text></xsl:if><xsl:if test="boolean($date/month)"><xsl:value-of select="$date/month"/></xsl:if></xsl:variable>
    
    <xsl:call-template name="comma-sequence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:choose>
          <xsl:when test="$dateformatted != ''">
            <xsl:apply-templates mode="article-item"
              select="source, issue, volume, $dateformatted, date/year, year, uri, pub-id" />
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates mode="article-item"
              select="source, issue, volume, date/year, year, uri, pub-id" />
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
    
    <!-- do the page range -->
    
    <xsl:choose>
      <xsl:when test="boolean(fpage) and boolean(lpage)">, pp. <xsl:value-of select="fpage" /> - <xsl:value-of select="lpage" /></xsl:when>
      <xsl:when test="boolean(fpage) and boolean(lpage) =  false">, p. <xsl:value-of select="fpage" /></xsl:when>
    </xsl:choose>
    
    <xsl:text>, reprint</xsl:text>
    <!--* except ($placed-names | $date |
      $titles | $conference)"/>-->
    
  </xsl:template>
  
  
  <!-- ============================================================= -->
  <!-- For publication types 'book' and 'dissertation'               -->
  <!-- ============================================================= -->
  
  <xsl:template name="book-citation-content">
    <xsl:variable name="all-names"
      select="(person-group|name|collab|anonymous|etal|string-name) /
      (. | nlm:fetch-comment(.))"/>
    <!-- $all-authors are all the elements that might be authors -->
    <xsl:variable name="placed-names"
      select="$all-names[not(preceding-sibling::* intersect
      (current()/* except $all-names))]"/>
    <!-- placed authors are all authors person-groups and all the
      elements that might be authors, except when they are 
      preceded by elements that can't be authors -->
    <xsl:variable name="date"
      select="date[1] |
      (year[1]|month[1]|day[1]|season[1])[not(exists(date))] |
      date-in-citation[1][not(exists(date|year|month|day|season))]"/>
    <!-- the date is either the first date element, or the first
      year, month, day elements when there is no date element -->
    <xsl:variable name="titles"
      select="(source | trans-source) / (. | nlm:fetch-comment(.))"/>
    <xsl:variable name="placed-title"
      select="$titles[1][not($placed-names)]"/>
    <xsl:variable name="title-info"
      select="(edition | edition/following-sibling::*[1][self::sup] |
      volume) / (. | nlm:fetch-comment(.)) |
      ($all-names except $placed-names)"/>
    
    <xsl:variable name="publisher"
      select="(publisher-loc | publisher-name | date/year | year)"/>
    
    <xsl:call-template name="format-names">
      <xsl:with-param name="names"
        select="$placed-names except comment"/>
    </xsl:call-template>
    
    <xsl:if test="not(exists($placed-names))">
      <!-- if we have no authors to place, we'll have a placed
        title, which we present before the date with the title 
        info -->
      <xsl:call-template name="book-title-sentence">
        <xsl:with-param name="titles" select="$placed-title"/>
        <xsl:with-param name="title-info" select="$title-info"/>
      </xsl:call-template>
    </xsl:if>
    
    <xsl:if test="exists($titles except $placed-title)">
      <!-- if we have any titles besides the placed title, we 
        put them directly after the date, with the title info 
        if we have no placed-title -->
      <xsl:call-template name="book-title-sentence">
        <xsl:with-param name="titles"
          select="$titles except $placed-title"/>
        <xsl:with-param name="title-info"
          select="$title-info[not($placed-title)]"/>
      </xsl:call-template>
    </xsl:if>
    
    <!-- we've now got all titles and title info, including all
      authors, volume and edition; now we do the publisher -->
    <xsl:call-template name="format-publisher">
      <xsl:with-param name="publisher" select="$publisher"/>
      <xsl:with-param name="dissertation"
        select="@publication-type='dissertation'"/>
    </xsl:call-template>
    
    <xsl:choose>
      <xsl:when test="boolean(uri)">, <xsl:apply-templates select="uri"/></xsl:when>
    </xsl:choose>
        
    
    <!-- if there's anything left we drop it in -->
    <xsl:call-template name="comma-sequence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:apply-templates mode="book-item"
          select="pub-id"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  
  
  <!-- ============================================================= -->
  <!-- For publication type 'book-chapter'                           -->
  <!-- ============================================================= -->
  
  <xsl:template name="book-chapter-citation-content">
    <xsl:variable name="all-names"
      select="(person-group|name|collab|anonymous|etal|string-name) /
      (. | nlm:fetch-comment(.))"/>
    <!-- $all-authors are all the elements that might be authors -->
    <xsl:variable name="placed-names"
      select="$all-names[not(preceding-sibling::* intersect
      (current()/* except $all-names))]"/>
    <!-- placed authors are all person-groups and all the
      elements that might be authors, except when they are 
      preceded by elements that can't be authors -->
    <xsl:variable name="date"
      select="date[1] |
      (year[1]|month[1]|day[1]|season[1])[not(exists(date))] |
      date-in-citation[1][not(exists(date|year|month|day|season))]"/>
    <!-- the date is either the first date element, or the first
      year, month, day elements when there is no date element -->
    <xsl:variable name="titles"
      select="(chapter-title | article-title | trans-title) /
      (. | nlm:fetch-comment(.))"/>
    <xsl:variable name="placed-title"
      select="$titles[1][not($placed-names)]"/>
    <xsl:variable name="book-info"
      select="(source | edition |
      edition/following-sibling::*[1]/self::sup | edition |
      volume | fpage | lpage | page-range) /
      (. | nlm:fetch-comment(.))"/>
    <xsl:variable name="publisher"
      select="(publisher-loc | publisher-name | date/year | year)"/>
    
    
    <xsl:call-template name="format-names">
      <xsl:with-param name="names"
        select="$placed-names except comment"/>
    </xsl:call-template>
    <xsl:if test="not(exists($placed-names))">
      <!-- if we have no authors to place, we'll have a placed
        title -->
      <xsl:apply-templates mode="article-title"
        select="$placed-title"/>
    </xsl:if>
    
    
    <xsl:apply-templates mode="article-title"
      select="$titles except ($placed-title | comment)"/>
    <!-- next we do the book info, which includes source,
      edition (w/ sup if it has any), volume, publisher-name,
      publisher-loc, and any comments directly following 
      these, plus any authors not included among
      $placed-authors. -->
    <xsl:call-template name="format-in-book">
      <xsl:with-param name="book-info" select="$book-info"/>
      <xsl:with-param name="book-names"
        select="$all-names except $placed-names"/>
    </xsl:call-template>
    
    <xsl:call-template name="format-publisher">
      <xsl:with-param name="publisher" select="$publisher"/>
    </xsl:call-template>
    
    <xsl:choose>
      <xsl:when test="boolean(uri)">, <xsl:apply-templates select="uri"/></xsl:when>
    </xsl:choose>
    
    <!-- do the page range -->
    
    <xsl:choose>
      <xsl:when test="boolean($book-info/self::fpage) and boolean($book-info/self::lpage)">, pp. <xsl:value-of select="$book-info/self::fpage" /> - <xsl:value-of select="$book-info/self::lpage" /></xsl:when>
      <xsl:when test="boolean($book-info/self::fpage) and boolean($book-info/self::lpage) =  false">, p. <xsl:value-of select="$book-info/self::fpage" /></xsl:when>
    </xsl:choose>
    
    <!-- if there's anything left we drop it in -->
    <xsl:call-template name="comma-sequence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:apply-templates mode="book-chapter-item"
          select="* except ($all-names | $date |
          $titles | $book-info | $publisher | uri)"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  
  
  <!-- ============================================================= -->
  <!-- Utility templates with generic specialty modes                         -->
  <!-- ============================================================= -->
  <!-- These templates are called by name and consolidate logic for
    processing chunks of the input, provided to them as parameters.
    Some of these are supported by templates in specialty modes. -->
  
  
  <xsl:template name="format-names">
    <xsl:param name="names" select="()"/>
    <xsl:choose>
      <xsl:when test="$names[self::person-group]">
        <!-- if $authors includes a person-group, we call 
          format-authors (recursively) with their contents 
          (except aff elements) plus the other authors -->
        <xsl:call-template name="format-names">
          <xsl:with-param name="names"
            select="$names/self::person-group/* |
            ($names[not(self::person-group)])"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <!-- otherwise, we have a bunch of
          (name|collab|anonymous|etal|string-name|aff)
          in document order -->
        <xsl:call-template name="punctuate-comma">
          <xsl:with-param name="contents">
            <xsl:call-template name="and-sequence">
              <xsl:with-param name="members" as="node()*">
                <xsl:apply-templates select="$names" mode="author"/>
              </xsl:with-param>
            </xsl:call-template>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  
  <xsl:template name="name-sequence">
    <!-- this template is very similar to format-authors, except it
      does not report authors' names in surname/given-names order,
      and it does not create a sentence, instead returning a
      root node to be spliced with other items in a sentence -->
    <xsl:param name="names" select="()"/>
    <xsl:choose>
      <xsl:when test="$names[self::person-group]">
        <!-- if $authors includes any person-group, we call ourself
          (recursively) with their contents (except aff elements) 
          plus the other authors -->
        <xsl:call-template name="name-sequence">
          <xsl:with-param name="names"
            select="$names/self::person-group/* |
            ($names[not(self::person-group)])"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <!-- otherwise, we have a bunch of
          (name|collab|anonymous|etal|string-name|aff)
          in document order -->
        <xsl:document>
          <xsl:call-template name="and-sequence">
            <xsl:with-param name="members"  as="node()*">
              <xsl:apply-templates select="$names"
                mode="author-western"/>
            </xsl:with-param>
          </xsl:call-template>
        </xsl:document>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  
  <!-- dispatches logic for amending a name list with -->
  <xsl:template name="author-type">
    <xsl:apply-templates mode="group-label"
      select="../@person-group-type[not(current()/following-sibling::*)]">
      <xsl:with-param name="plural"
        select="exists(preceding-sibling::*[not(self::aff)])"/>
    </xsl:apply-templates>
  </xsl:template>
  
  
  <!-- 'author' mode formats structured name elements for the 
    utility templates -->
  <xsl:template match="name" mode="author">
    <xsl:document>
      <xsl:apply-templates select="surname" mode="format"/>
      <xsl:if test="given-names">
        <xsl:text>, </xsl:text>
        <xsl:apply-templates select="given-names" mode="format"/>
      </xsl:if>
        <xsl:for-each select="suffix">
          <xsl:text>, </xsl:text>
        <xsl:apply-templates select="." mode="format"/>
      </xsl:for-each>
      <xsl:call-template name="author-type"/>
      <xsl:apply-templates select="nlm:fetch-comment(.)"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="name" mode="author-western">
    <xsl:document>
      <xsl:apply-templates select="given-names" mode="format"/>
      <xsl:text> </xsl:text>
      <xsl:apply-templates select="surname" mode="format"/>
      <xsl:for-each select="suffix">
        <xsl:text> </xsl:text>
        <xsl:apply-templates select="." mode="format"/>
      </xsl:for-each>
      <xsl:call-template name="author-type"/>
      <xsl:apply-templates select="nlm:fetch-comment(.)"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="collab" mode="author author-western">
    <xsl:document>
      <xsl:apply-templates select="." mode="format"/>
      <xsl:call-template name="author-type"/>
      <xsl:apply-templates select="nlm:fetch-comment(.)"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="anonymous" mode="author author-western">
    <xsl:document>
      <xsl:text>Anonymous</xsl:text>
      <xsl:call-template name="author-type"/>
      <xsl:apply-templates select="nlm:fetch-comment(.)"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="etal" mode="author author-western">
    <xsl:document>
      <xsl:text>et al.</xsl:text>
      <xsl:call-template name="author-type"/>
      <xsl:apply-templates select="nlm:fetch-comment(.)"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="string-name" mode="author author-western">
    <xsl:document>
      <xsl:apply-templates select="." mode="format"/>
      <xsl:call-template name="author-type"/>
      <xsl:apply-templates select="nlm:fetch-comment(.)"/>
    </xsl:document>
  </xsl:template>
  
  <xsl:template match="aff" mode="author author-western"/>
  <!-- dropping aff, as APA has no provision for an affiliation with an author name -->
  
  
  <xsl:template match="@person-group-type" mode="group-label">
    <!-- ordinarily we just drop this -->
  </xsl:template>
  
  
  <xsl:template mode="group-label"
    match="@person-group-type[.='editor']">
    <xsl:param name="plural" select="false()"/>
    <xsl:param name="in-paren" select="false()" tunnel="yes"/>
    <xsl:if test="$in-paren">,</xsl:if>
    <xsl:text> </xsl:text>
    <xsl:if test="not($in-paren)">(</xsl:if>
    <xsl:text>ed</xsl:text>
    <xsl:if test="$plural">s</xsl:if>
    <xsl:text>.</xsl:text>
    <xsl:if test="not($in-paren)">)</xsl:if>
  </xsl:template>
  
  <xsl:template mode="group-label"
    match="@person-group-type[.='translator']">
    <xsl:param name="in-paren" select="false()" tunnel="yes"/>
    <xsl:if test="$in-paren">,</xsl:if>
    <xsl:text> </xsl:text>
    <xsl:if test="not($in-paren)">(</xsl:if>
    <xsl:text>Trans.</xsl:text>
    <xsl:if test="not($in-paren)">)</xsl:if>
  </xsl:template>
  
  
  <xsl:template match="article-title | chapter-title | trans-title"
    mode="article-title">
    <xsl:call-template name="punctuate-comma">
      <xsl:with-param name="contents">
        "<xsl:apply-templates mode="format"
          select=". | nlm:fetch-comment(.)"/>"</xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  
  
  <xsl:template mode="article-title"
    match="trans-title[exists(../article-title|../chapter-title)]">
    <!-- overrides regular handling when a trans-title appears with 
      an article or chapter title -->
    <xsl:call-template name="punctuate-comma">
      <xsl:with-param name="contents">
        <xsl:text>[</xsl:text>
        <xsl:apply-templates select=". | nlm:fetch-comment(.)" mode="format"/>
        <xsl:text>]</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  
  
  <xsl:template name="format-date">
    <xsl:param name="date" select="()"/>
    <xsl:if test="exists($date)">
      <xsl:choose>
        <xsl:when test="$date/self::date">
          <xsl:call-template name="format-date">
            <xsl:with-param name="date" select="$date/*"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:call-template name="punctuate-sentence">
            <xsl:with-param name="contents">
              <xsl:text>(</xsl:text>
              <xsl:for-each
                select="$date/(self::year|self::conf-date|
                self::date-in-citation)">
                <xsl:apply-templates select="." mode="format"/>
                <xsl:if test="position() lt last()">
                  <xsl:text>, </xsl:text>
                </xsl:if>
              </xsl:for-each>
              <xsl:for-each
                select="$date[not(self::year|self::conf-date|
                self::date-in-citation)]">
                <xsl:if test="position() = 1">, </xsl:if>
                <xsl:text> </xsl:text>
                <xsl:apply-templates select="." mode="format"/>
              </xsl:for-each>
              <xsl:text>)</xsl:text>
            </xsl:with-param>
          </xsl:call-template>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>
  
  
  <xsl:template name="format-publisher">
    <xsl:param name="publisher" select="()"/>
    <xsl:param name="dissertation" select="false()"/>
    
    <xsl:if test="exists($publisher)">
      (<xsl:if test="$dissertation">Doctoral dissertation, </xsl:if>
      <xsl:call-template name="colon-sequence">
        <xsl:with-param name="phrases">
          <xsl:apply-templates mode="format"
            select="$publisher/self::publisher-loc"/>
        </xsl:with-param>
      </xsl:call-template>
      
      <xsl:if test="$publisher/
        (self::publisher-loc)">: </xsl:if>
      <xsl:call-template name="comma-sequence">
        <xsl:with-param name="phrases">
          <xsl:apply-templates mode="format"
            select="$publisher/self::publisher-name"/>
        </xsl:with-param>
      </xsl:call-template>
      
      <xsl:if test="$publisher/self::year">, </xsl:if>
      
      <xsl:call-template name="comma-sequence">
        <xsl:with-param name="phrases">
          <xsl:apply-templates mode="format"
            select="$publisher/self::date/year | $publisher/self::year"/>
        </xsl:with-param>
      </xsl:call-template>)</xsl:if>
  </xsl:template>
  
  
  <xsl:template name="book-title-sentence">
    <xsl:param name="titles" select="()"/>
    <!-- titles will be source and/or trans-title -->
    <xsl:param name="title-info" select="()"/>
    <!-- title info will be any additional authors, volume,
      edition, fpage, lpage or page-range -->
    <xsl:variable name="first-title" select="$titles[1]"/>
    <xsl:call-template name="format-book-title">
      <xsl:with-param name="title" select="$first-title"/>
      <xsl:with-param name="title-info" select="$title-info"/>
      <xsl:with-param name="other-titles"
        select="$titles except $first-title"/>
    </xsl:call-template>
  </xsl:template>
  
  
  <xsl:template name="format-book-title">
    <xsl:param name="title" select="()"/>
    <xsl:param name="title-info" select="()"/>
    <xsl:param name="other-titles" select="()"/>
    <xsl:document>
      <xsl:apply-templates select="$title" mode="format"/>
      <xsl:if test="$title-info | $other-titles">
        <xsl:text> (</xsl:text>
        <xsl:call-template name="comma-sequence">
          <xsl:with-param name="phrases" as="node()*">
            <xsl:apply-templates mode="book-item"
              select="$title-info | $other-titles"/>
          </xsl:with-param>
        </xsl:call-template>
        <xsl:text>)</xsl:text>
      </xsl:if>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template name="format-in-book">
    <xsl:param name="book-info" select="()"/>
    <!-- includes source, edition (w/ sup if it has any),
      volume, and any comments directly following these -->
    <xsl:param name="book-names" select="()"/>
    <!-- includes any authors not included among
      $placed-authors (which should generally
      be editors, translators and the like) -->
    <xsl:text>in </xsl:text>
    <xsl:call-template name="comma-sequence">
      <xsl:with-param name="phrases" as="node()*">
        <xsl:variable name="name-sequence">
          <xsl:call-template name="name-sequence">
            <xsl:with-param name="names" select="$book-names"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:copy-of select="$name-sequence[normalize-space()]"/>
        
        <xsl:call-template name="format-book-title">
          <xsl:with-param name="title"
            select="$book-info/(self::source|self::trans-source)"/>
          <xsl:with-param name="title-info"
            select="$book-info/(self::edition)"/>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  
  
  <xsl:template name="and-sequence">
    <!-- Generates a sequence of items punctuated with commas and/or
      an '&'. The '&' appears preceding the last item unless it has the
      value 'et al.', in which case only a comma appears. The 
      Oxford comma (a comma with the '&' preceding the last item)
      appears unless there are only two items and the first item
      does not contain a comma. -->
    
    <!-- So:
      The sequence 'Sappho', 'et al.' comes out
      "Sappho, et al."
      The sequence 'Sappho', 'Anacreon' comes out
      "Sappho & Anacreon"
      The sequence 'Sappho', 'Anacreon' and 'Semonides' comes out
      "Sappho, Anacreon, & Semonides"
      The sequence 'Mantle, M.' and 'Ruth, B.' comes out
      "Mantle, M., & Ruth, B."
      The sequence 'Lowell, P.' and 'Copernicus' comes out
      "Lowell, P., & Copernicus"
      The sequence 'Copernicus' and 'Lowell, P.' comes out
      "Copernicus & Lowell, P." -->
    <xsl:param name="members" select="()"/>
    <xsl:for-each select="$members[normalize-space(.)]">
      <xsl:variable name="pos" select="position()"/>
      <xsl:variable name="etal" select="contains(.,'et al.')"/>
      <xsl:if test="$pos gt 1">
        <xsl:choose>
          <xsl:when test="$pos = last()">
            <xsl:if test="($pos gt 2) or $etal or
              contains($members[$pos - 1],',')">, </xsl:if>
            <xsl:if test="not($etal)"> &amp; </xsl:if>
          </xsl:when>
          <xsl:otherwise>, </xsl:otherwise>
        </xsl:choose>
      </xsl:if>
      <xsl:copy-of select="."/>
    </xsl:for-each>
  </xsl:template>
  
  
  <xsl:template name="comma-sequence">
    <xsl:param name="phrases" select="()"/>
    <xsl:for-each select="$phrases">
      <xsl:if test="position() gt 1">, </xsl:if>
      <xsl:copy-of select="."/>
    </xsl:for-each>
  </xsl:template>
  
  <xsl:template name="colon-sequence">
    <xsl:param name="phrases" select="()"/>
    <xsl:for-each select="$phrases">
      <xsl:if test="position() gt 1">: </xsl:if>
      <xsl:copy-of select="."/>
    </xsl:for-each>
  </xsl:template>
  
  
  <!-- Punctuates with a period. Does not punctuate strings 
    that are already punctuated. -->
  <xsl:template name="punctuate-sentence">
    <xsl:param name="contents" select="()"/>
    <xsl:variable name="already-sentence-expr">
      <xsl:text><!--
        ends in . ! or ? -->^.*[!\.\?]$|<!--
          ends in ! . or ? inside parens, brackets or braces
        -->^\p{Ps}.*[!\.\?]\p{Pe}$</xsl:text>
    </xsl:variable>
    
    <xsl:copy-of select="$contents"/>
    <xsl:if test="normalize-space($contents)">
      <xsl:if test="not(matches(normalize-space($contents),
        $already-sentence-expr))">
        <xsl:text>.</xsl:text>
      </xsl:if>
      <xsl:text> </xsl:text>
    </xsl:if>
  </xsl:template>
  
  
  
  <!-- Punctuates with a comma. Does not punctuate strings 
    that are already punctuated. -->
  <xsl:template name="punctuate-comma">
    <xsl:param name="contents" select="()"/>
    <xsl:variable name="already-sentence-expr">
      <xsl:text><!--
        ends in . ! or ? -->^.*[!\.\?]$|<!--
          ends in ! . or ? inside parens, brackets or braces
        -->^\p{Ps}.*[!\.\?]\p{Pe}$</xsl:text>
    </xsl:variable>
    
    <xsl:copy-of select="$contents"/>
    <xsl:if test="normalize-space($contents)">
      <xsl:if test="not(matches(normalize-space($contents),
        $already-sentence-expr))">
        <xsl:text>,</xsl:text>
      </xsl:if>
      <xsl:text> </xsl:text>
    </xsl:if>
  </xsl:template>
  
  
  <!-- Punctuates with a period, demarcating separate items
    with commas while doing so -->
  <xsl:template name="comma-sequence-sentence">
    <xsl:param name="phrases" as="node()*"/>
    <xsl:call-template name="punctuate-sentence">
      <xsl:with-param name="contents">
        <xsl:call-template name="comma-sequence">
          <xsl:with-param name="phrases" select="$phrases"/>
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  
  
  <!-- ============================================================= -->
  <!-- 'format' mode                                                 -->
  <!-- ============================================================= -->
  <!-- "format" mode: maps arbitrary citation element contents into
    formatted equivalents in the "simple citation" element subset -->
  
  
  <xsl:template mode="format" match="*">
    <xsl:apply-templates mode="format"/>
  </xsl:template>
  
  
  <xsl:template mode="format" match="person-group | name | date">
    <xsl:apply-templates select="*" mode="format"/>
  </xsl:template>
  
  
  <xsl:template mode="format"
    match="string-name/text()
    [not(preceding-sibling::*) or not(following-sibling::*)]
    [not(normalize-space())]"/>
  <!-- whitespace before the first element or after the last is trimmed from string-name -->
  
  
  <xsl:template mode="format"
    match="bold | italic | monospace | overline | roman |
    sans-serif | sc | strike | underline | inline-graphic |
    label | email | ext-link | uri | sub | sup | 
    styled-content">
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates mode="format"/>
    </xsl:copy>
  </xsl:template>
  
  
  <xsl:template mode="format" match="source">
    <italic>
      <xsl:apply-templates mode="format"/>
    </italic>
  </xsl:template>
  
  <xsl:template mode="format" match="pub-id[@pub-id-type=('DOI','doi')]">
    <uri>http://dx.doi.org/<xsl:apply-templates mode="format"/></uri>
  </xsl:template>
  
  <xsl:template mode="format" match="pub-id[@pub-id-type=('PMID','pmid')]">
    <xsl:text>pubmed id:</xsl:text>
    <xsl:apply-templates mode="format"/>
  </xsl:template>
  
  <xsl:template mode="format" match="pub-id[@pub-id-type=('PMC-ID','pmc-id')]">
    <xsl:text>pmc id:</xsl:text>
    <xsl:apply-templates mode="format"/>
  </xsl:template>
  
  <xsl:template mode="format" match="pub-id[@pub-id-type=('DOAJ','doaj')]">
    <xsl:text>doaj:</xsl:text>
    <xsl:apply-templates mode="format"/>
  </xsl:template>
  
  <xsl:template mode="format" match="pub-id[@pub-id-type=('CODEN','coden')]">
    <xsl:text>coden:</xsl:text>
    <xsl:apply-templates mode="format"/>
  </xsl:template>
  
  
  
  <!-- =============================================================== -->
  <!-- Specialty modes for each citation type                          -->
  <!-- =============================================================== -->
  
  <!-- Three 'item' modes, 'article-item', 'book-item' and 
    'book-chapter-item', generate single items for further 
    punctuation; in some cases this involves arranging and 
    punctuating related elements belonging together,
    e.g. volume/issue, fpage/lpage.
    
    Each template in 'item' mode must return a single item;
    hence, any results that may include more than one node are 
    collected in local root nodes by means of xsl:document -->
  
  
  <xsl:template mode="article-item book-item book-chapter-item"
    match="*">
    <xsl:document>
      <xsl:apply-templates select="." mode="format"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template mode="article-item book-item"
    match="lpage[preceding-sibling::*[1]/self::fpage]">
    <!-- dropped, because picked up with the fpage -->
  </xsl:template>
  
  
  <xsl:template match="fpage" mode="article-item">
    <xsl:document>
      <xsl:apply-templates select="." mode="format"/>
      <xsl:for-each select="following-sibling::*[1]/
        self::lpage[not(.=current())]">
        <!-- grabbing the next sibling if it's an lpage
          not equal the fpage -->
        <xsl:text>-</xsl:text>
        <xsl:apply-templates select="." mode="format"/>
      </xsl:for-each>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="fpage" mode="book-item">
    <xsl:document>
      <xsl:variable name="lpage">
        <xsl:for-each
          select="following-sibling::*[1]/self::lpage[not(.=current())]">
          <xsl:text>-</xsl:text>
          <xsl:apply-templates select="." mode="format"/>
        </xsl:for-each>
      </xsl:variable>
      <xsl:text>p</xsl:text>
      <xsl:if test="normalize-space($lpage)">p</xsl:if>
      <xsl:text>. </xsl:text>
      <xsl:apply-templates select="." mode="format"/>
      <xsl:copy-of select="$lpage"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template mode="article-item book-item" match="page-range">
    <xsl:document>
      <xsl:text>pp. </xsl:text>
      <xsl:apply-templates select="." mode="format"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="source" mode="article-item">
    <xsl:document>
      <xsl:apply-templates select="." mode="format"/>
      <xsl:apply-templates mode="edition"
        select="following-sibling::*[1]/self::edition"/>
      <xsl:for-each select="../issue[not(../(volume))][1]">
        <!-- pick up the first issue if there is no volume -->
        <xsl:text> [</xsl:text>
        <xsl:apply-templates select="." mode="format"/>
        <xsl:for-each select="../(issue|supplement) except .">
          <xsl:text>, </xsl:text>
          <xsl:apply-templates select="." mode="format"/>
        </xsl:for-each>
        <xsl:text>]</xsl:text>
      </xsl:for-each>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="edition" mode="edition">
    <xsl:text> (</xsl:text>
    <xsl:apply-templates select="." mode="format"/>
    <xsl:apply-templates
      select="following-sibling::*[1]/self::sup /
      (. | nlm:fetch-comment(.))"
      mode="format"/>
    <xsl:if test="not(contains(lower-case(.),'ed'))"> ed.</xsl:if>
    <xsl:text>)</xsl:text>
  </xsl:template>
  
  
  <xsl:template match="sup[preceding-sibling::*[1]/self::edition]"
    mode="article-item book-item"/>
  <!-- handled with the preceding-sibling edition -->
  
  
  <xsl:template match="volume" mode="article-item">
    <xsl:document>
      <xsl:apply-templates select="." mode="format"/>
      <xsl:for-each select="../(issue|supplement)[1]">
        <!-- pick up the issue and/or supplement if there is no volume -->
        <xsl:call-template name="issue"/>
      </xsl:for-each>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template mode="article-item" priority="3"
    match="issue[../(volume|source)]">
    <!-- dropped, because picked up with volume or source-->
  </xsl:template>
  
  
  <xsl:template mode="article-item" priority="3"
    match="supplement[../volume|../source[../issue]]">
    <!-- dropped, because picked up with volume or source -->
  </xsl:template>
  
  
  <xsl:template mode="article-item" priority="2"
    match="issue[preceding-sibling::supplement] |
    supplement[preceding-sibling::issue]">
    <!-- dropped, because picked up with the first preceding sibling issue or supplement -->
  </xsl:template>
  
  
  <xsl:template mode="article-item" name="issue"
    match="issue | supplement">
    <!-- only matches the first issue when there is no volume
      or source, or supplement when there is no volume -->
    <xsl:document>
      <xsl:text>(</xsl:text>
      <xsl:apply-templates select="." mode="format"/>
      <xsl:for-each select="../(issue|supplement) except .">
        <xsl:text>, </xsl:text>
        <xsl:apply-templates select="." mode="format"/>
      </xsl:for-each>
      <xsl:text>)</xsl:text>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template mode="article-item"
    match="edition[preceding-sibling::*[1]/self::source]">
    <!-- dropped, because picked up with source -->
  </xsl:template>
  
  
  <xsl:template match="conf-name" mode="article-item">
    <xsl:document>
      <xsl:text>Paper presented at </xsl:text>
      <xsl:apply-templates select="." mode="format"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="person-group" mode="book-item">
    <xsl:document>
      <xsl:call-template name="and-sequence">
        <xsl:with-param name="members" as="node()*">
          <xsl:apply-templates select="*" mode="author">
            <xsl:with-param name="in-paren" tunnel="yes" select="true()"/>
          </xsl:apply-templates>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:template match="edition" mode="book-item">
    <xsl:document>
      <xsl:apply-templates select="." mode="format"/>
      <xsl:apply-templates select="following-sibling::*[1]/self::sup"
        mode="format"/>
      <xsl:if test="not(contains(lower-case(.),'ed'))"> ed.</xsl:if>
    </xsl:document>
  </xsl:template>
  <xsl:template match="volume" mode="book-item book-chapter-item">
    <xsl:document>
      <xsl:text>Vol</xsl:text>
      <xsl:if test="not(matches(normalize-space(),
        '^\p{N}+$|^[MCLXVI]+$|^[mclxvi]+$'))">
        <xsl:text>s</xsl:text>
      </xsl:if>
      <!-- plural if not only a number (including Roman numerals) -->
      <xsl:text>. </xsl:text>
      <xsl:apply-templates select="." mode="format"/>
    </xsl:document>
  </xsl:template>
  
  
  <xsl:function name="nlm:fetch-comment" as="element(comment)?">
    <!-- given any element, retrieves a comment element that follows
      it immediately and matches the $bracketed-text expression, 
      as provision for punctuating them together -->
    <xsl:param name="e" as="element()"/>
    <xsl:variable name="bracketed-text" select="'^\(.*\)$|^\[.*\]$'"/>
    <!-- $bracketed-text provides a regular expression matching 
      strings wrapped in either parentheses or square brackets -->
    <xsl:sequence select="$e/following-sibling::*[1]/self::comment
      [matches(normalize-space(),$bracketed-text)]"/>
  </xsl:function>
  
  
  <!-- ============================================================= -->
  <!-- End stylesheet                                                -->
  <!-- ============================================================= -->
  
</xsl:stylesheet>

