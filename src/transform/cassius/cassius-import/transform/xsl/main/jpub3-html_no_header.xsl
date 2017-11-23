<?xml version="1.0"?>
<!-- ============================================================= -->
<!--  MODULE:    HTML Preview of Journal Publishing 3.0 XML        -->
<!--  VERSION:   1.0                                               -->
<!--  DATE:      October-December 2008                             -->
<!--                                                               -->
<!-- ============================================================= -->

<!-- ============================================================= -->
<!--  SYSTEM:    NCBI Archiving and Interchange Journal Articles   -->
<!--                                                               -->
<!--  PURPOSE:   Provide an HTML preview of a journal article,     -->
<!--             in a form suitable for reading.                   -->
<!--                                                               -->
<!--  PROCESSOR DEPENDENCIES:                                      -->
<!--             None: standard XSLT 1.0                           -->
<!--             Tested using Saxon 6.5, Tranformiix (Firefox),    -->
<!--               Saxon 9.1.0.3                                   -->
<!--                                                               -->
<!--  COMPONENTS REQUIRED:                                         -->
<!--             1) This stylesheet                                -->
<!--             2) CSS styles defined in jpub-preview.css         -->
<!--                (to be placed with the results)                -->
<!--                                                               -->
<!--  INPUT:     An XML document valid to the                      -->
<!--             Journal Publishing 3.0 DTD.                       -->
<!--             (And note further assumptions and limitations     -->
<!--             below.)                                           -->
<!--                                                               -->
<!--  OUTPUT:    HTML (XHTML if a postprocessor is used)           -->
<!--                                                               -->
<!--  CREATED FOR:                                                 -->
<!--             Digital Archive of Journal Articles               -->
<!--             National Center for Biotechnology Information     -->
<!--                (NCBI)                                         -->
<!--             National Library of Medicine (NLM)                -->
<!--                                                               -->
<!--  CREATED BY:                                                  -->
<!--             Wendell Piez (based on HTML design by             -->
<!--             Kate Hamilton and Debbie Lapeyre, 2004),          -->
<!--             Mulberry Technologies, Inc.                       -->
<!--                                                               -->
<!-- ============================================================= -->

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:mml="http://www.w3.org/1998/Math/MathML"
  xmlns:xslt="http://xml.apache.org/xslt"
  xmlns="http://www.w3.org/1999/xhtml"
  exclude-result-prefixes="xlink mml">


<!--  <xsl:output method="xhtml" indent="yes" omit-xml-declaration="no" encoding="UTF-8"
    doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"
    doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"/>-->


  <!--<xsl:output doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
    doctype-system="http://www.w3.org/TR/html4/loose.dtd"
    encoding="UTF-8"/>-->
 
  <xsl:strip-space elements="*"/>

  <!-- Space is preserved in all elements allowing #PCDATA -->
  <xsl:preserve-space
    elements="abbrev abbrev-journal-title access-date addr-line aff 
              alt-text alt-title article-id article-title attrib 
              award-id bold chapter-title chem-struct collab comment 
              compound-kwd-part conf-acronym conf-date conf-loc conf-name 
              conf-num conf-sponsor conf-theme copyright-holder 
              copyright-statement copyright-year corresp country 
              date-in-citation day def-head degrees disp-formula 
              edition elocation-id email etal ext-link fax fpage 
              funding-source funding-statement given-names glyph-data gov 
              inline-formula inline-supplementary-material institution 
              isbn issn issue issue-id issue-part issue-sponsor 
              issue-title italic journal-id journal-subtitle 
              journal-title kwd label license-p long-desc lpage 
              meta-name meta-value mixed-citation monospace month 
              named-content object-id on-behalf-of overline p 
              page-range part-title patent phone prefix preformat 
              price principal-award-recipient principal-investigator 
              product pub-id publisher-loc publisher-name 
              related-article related-object role roman sans-serif 
              sc season self-uri series series-text series-title 
              sig sig-block size source speaker std strike 
              string-conf string-date string-name styled-content sub 
              subject subtitle suffix sup supplement surname target 
              td term term-head tex-math textual-form th time-stamp 
              title trans-source trans-subtitle trans-title underline 
              unstructured-kwd-group uri verse-line volume volume-id 
              volume-series x xref year 

              mml:annotation mml:ci mml:cn mml:csymbol mml:mi mml:mn 
              mml:mo mml:ms mml:mtext"/>


  <xsl:param name="css" select="'jpub-preview.css'"/>


  <!-- Keys -->

  <!-- To reduce dependency on a DTD for processing, we declare
       a key to use instead of the id() function. -->
  <xsl:key name="element-by-id" match="*[@id]" use="@id"/>

  <!-- Enabling retrieval of cross-references to objects -->
  <xsl:key name="xref-by-rid" match="xref" use="@rid"/>
  
  <!-- ============================================================= -->
  <!--  ROOT TEMPLATE - HANDLES HTML FRAMEWORK                       -->
  <!-- ============================================================= -->

  
  <xsl:template match="/">
        <xsl:apply-templates/>
  </xsl:template>


  <xsl:template name="make-html-header">
    <head>
      <title>
        <xsl:variable name="authors">
          <xsl:call-template name="author-string"/>
        </xsl:variable>
        <xsl:value-of select="normalize-space($authors)"/>
        <xsl:if test="normalize-space($authors)">: </xsl:if>
        <xsl:value-of
          select="/article/front/article-meta/title-group/article-title[1]"/>
      </title>
      <!--<link rel="stylesheet" type="text/css" href="{$css}"/>-->
      <!-- XXX check: any other header stuff? XXX -->
    </head>
  </xsl:template>


<!-- ============================================================= -->
<!--  TOP LEVEL                                                    -->
<!-- ============================================================= -->

  <!--
      content model for article:
         (front,body?,back?,floats-group?,(sub-article*|response*))
      
      content model for sub-article:
         ((front|front-stub),body?,back?,floats-group?,
          (sub-article*|response*))
      
      content model for response:
         ((front|front-stub),body?,back?,floats-group?) -->
  
  <xsl:template match="article">
    <xsl:call-template name="make-article"/>
  </xsl:template>

  <xsl:template match="sub-article | response">
    <hr class="part-rule"/>
    <xsl:call-template name="make-article"/>
  </xsl:template>


<!-- ============================================================= -->
<!--  "make-article" for the document architecture                 -->
<!-- ============================================================= -->

  <xsl:template name="make-article">
    <!-- Generates a series of (flattened) divs for contents of any
	       article, sub-article or response -->

    <!-- variable to be used in div id's to keep them unique -->
    <xsl:variable name="this-article">
      <xsl:apply-templates select="." mode="id"/>
    </xsl:variable>

    <div id="{$this-article}-front" class="front">
      <xsl:apply-templates select="front | front-stub"/>
    </div>

    <!-- body -->
    <xsl:for-each select="body">
      <div id="{$this-article}-body" class="body">
        <xsl:apply-templates/>
      </div>
    </xsl:for-each>

    <xsl:if test="back | $loose-footnotes">
      <!-- $loose-footnotes is defined below as any footnotes outside
           front matter or fn-group -->
      <div id="{$this-article}-back" class="back">
        <xsl:call-template name="make-back"/>
      </div>
    </xsl:if>

    <xsl:for-each select="floats-group">
      <div id="{$this-article}-floats" class="back">
        <xsl:call-template name="main-title">
          <xsl:with-param name="contents">
            <span class="generated">Floating objects</span>
          </xsl:with-param>
        </xsl:call-template>
        <xsl:apply-templates/>
      </div>
    </xsl:for-each>

    <!-- more metadata goes in the footer -->
    <div id="{$this-article}-footer" class="footer">
      <xsl:call-template name="footer-metadata"/>
    </div>

    <!-- sub-article or response (recursively calls
		     this template) -->
    <xsl:apply-templates select="sub-article | response"/>

  </xsl:template>

  <xsl:template match="front | front-stub">
    <div id="article_meta">
        <!-- Cell 2: Article information -->
        <xsl:for-each select="article-meta | self::front-stub">
          <!-- content model:
				    (article-id*, article-categories?, title-group,
				     (contrib-group | aff)*, 
             author-notes?, pub-date+, volume?, volume-id*,
             volume-series?, issue?, issue-id*, issue-title*,
             issue-sponsor*, issue-part?, isbn*, supplement?, 
             ((fpage, lpage?, page-range?) | elocation-id)?, 
             (email | ext-link | uri | product | 
              supplementary-material)*, 
             history?, permissions?, self-uri*, related-article*, 
             abstract*, trans-abstract*, 
             kwd-group*, funding-group*, conference*, counts?,
             custom-meta-group?)
            
            These are handled as follows:

            In the "Article Information" header cell:
              article-id
              pub-date
              volume
              volume-id
              volume-series
              issue
              issue-id
              issue-title
              issue-sponsor
              issue-part
              isbn
              supplement
              fpage
              lpage
              page-range
              elocation-id
              email
              ext-link
              uri
              product
              history
              permissions
              self-uri
              related-article
              funding-group
              conference

            In the "Article title" cell:
              title-group
              contrib-group
              aff
              author-notes
              abstract
              trans-abstract

            In the metadata footer
              article-categories
              supplementary-material
              kwd-group
              counts
              custom-meta-group

				  -->
            <h4 class="generated">
              <xsl:text>Article Information</xsl:text>
            </h4>
            <div class="metadata-group">

              <xsl:apply-templates mode="metadata"
                select="email | ext-link | uri | self-uri"/>

              <xsl:apply-templates mode="metadata" select="product"/>

              <xsl:apply-templates mode="metadata" select="permissions"/>

              <xsl:apply-templates mode="metadata" select="history/date"/>

              <xsl:apply-templates mode="metadata" select="pub-date"/>

              <xsl:call-template name="volume-info">
                <!-- handles volume?, volume-id*, volume-series? -->
              </xsl:call-template>

              <xsl:call-template name="issue-info">
                <!-- handles issue?, issue-id*, issue-title*,
                     issue-sponsor*, issue-part? -->
              </xsl:call-template>

              <xsl:call-template name="page-info">
                <!-- handles (fpage, lpage?, page-range?) -->
              </xsl:call-template>

              <xsl:apply-templates mode="metadata" select="elocation-id"/>

              <xsl:apply-templates mode="metadata" select="isbn"/>

              <xsl:apply-templates mode="metadata"
                select="supplement | related-article | conference"/>

              <xsl:apply-templates mode="metadata" select="article-id"/>

              <xsl:apply-templates mode="metadata" select="funding-group/*">
                <!-- includes (award-group*, funding-statement*,
                     open-access?) -->
              </xsl:apply-templates>
            </div>
        </xsl:for-each>
   
          <hr class="part-rule"/>
       

      <!-- change context to front/article-meta (again) -->
      <xsl:for-each select="article-meta | self::front-stub">

            <xsl:apply-templates mode="metadata" select="title-group"/>

        <xsl:apply-templates mode="metadata" select="contrib-group"/>
        <!-- back in article-meta or front-stub context -->
        <xsl:if test="aff | author-notes">

              <div class="metadata-group">
                <xsl:apply-templates mode="metadata"
                  select="aff | author-notes"/>
              </div>

        </xsl:if>
        <!-- abstract(s) -->
        <xsl:if test="abstract | trans-abstract">
          <!-- rule separates title+authors from abstract(s) -->
              <hr class="section-rule"></hr>
          <xsl:for-each select="abstract | trans-abstract">
            <!-- title in left column, content (paras, secs) in right -->

                <h4 class="callout-title">
                  <xsl:apply-templates select="title/node()"/>
                  <xsl:if test="not(normalize-space(title))">
                    <span class="generated">
                      <xsl:if test="self::trans-abstract">Translated </xsl:if>
                      <xsl:text>Abstract</xsl:text>
                    </span>
                  </xsl:if>
                </h4>

                <xsl:apply-templates select="*[not(self::title)]"/>

          </xsl:for-each>
          <!-- end of abstract or trans-abstract -->
        </xsl:if>
        <!-- end of dealing with abstracts -->
      </xsl:for-each>
      <xsl:for-each select="notes">

            <div class="metadata-group">
              <xsl:apply-templates mode="metadata" select="."/>
            </div>

      </xsl:for-each>

          <!-- part-rule ending this table, separating it from the
              title-and-authors table -->
          <hr class="part-rule"></hr>

    </div>
    <!-- end of big front-matter pull -->
  </xsl:template>
  
  <xsl:template name="footer-metadata">
    <!-- handles: article-categories, kwd-group, counts, 
           supplementary-material, custom-meta-group
         Plus also generates a sheet of processing warnings
         -->
    <xsl:for-each select="front/article-meta | front-stub">
      <xsl:if test="article-categories | kwd-group | counts |
                    supplementary-material | custom-meta-group">
      <table width="100%" class="metadata">
        <tr>
          <td>
            <hr class="part-rule"></hr>
          </td>
        </tr>
        <tr>
          <td>
            <h4 class="generated">
              <xsl:text>Article Information (continued)</xsl:text>
            </h4>
            <div class="metadata-group">
              <xsl:apply-templates mode="metadata"
                select="supplementary-material"/>

              <xsl:apply-templates mode="metadata"
                select="article-categories | kwd-group | counts"/>

              <xsl:apply-templates mode="metadata" select="custom-meta-group"/>
            </div>
          </td>
        </tr>
      </table>
      </xsl:if>
    </xsl:for-each>

    <xsl:variable name="process-warnings">
      <xsl:call-template name="process-warnings"/>
    </xsl:variable>

    <xsl:if test="normalize-space($process-warnings)">
      <table width="100%" class="metadata">
        <tr>
          <td>
            <hr class="part-rule"></hr>
          </td>
        </tr>
        <tr>
          <td>
            <h4 class="generated">
              <xsl:text>Process warnings</xsl:text>
            </h4>
            <p>Warnings reported by the processor due to anomalous or incomplete markup follow:</p>
            <div class="metadata-group">
              <xsl:copy-of select="$process-warnings"/>
            </div>
          </td>
        </tr>
      </table>
    </xsl:if>
  </xsl:template>


<!-- ============================================================= -->
<!--  METADATA PROCESSING                                          -->
<!-- ============================================================= -->

<!--  Includes mode "metadata" for front matter, along with 
      "metadata-inline" for metadata elements collapsed into 
      inline sequences, plus associated named templates            -->

  <!-- journal-meta content:
       journal-id+, journal-title-group*, issn+, isbn*, publisher?,
       notes? -->

  <xsl:template match="journal-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Journal ID</xsl:text>
        <xsl:for-each select="@journal-id-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="journal-title-group" mode="metadata">
    <xsl:apply-templates mode="metadata"/>
  </xsl:template>


  <xsl:template match="issn" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>ISSN</xsl:text>
        <xsl:call-template name="append-pub-type"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="isbn" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>ISBN</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="publisher" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
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
    <span class="generated"> (</span>
    <xsl:apply-templates/>
    <span class="generated">)</span>
  </xsl:template>


  <xsl:template match="notes" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Notes</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <!-- journal-title-group content:
       (journal-title*, journal-subtitle*, trans-title-group*,
       abbrev-journal-title*) -->

  <xsl:template match="journal-title" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Title</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="journal-subtitle" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Subtitle</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="trans-title-group" mode="metadata">
    <xsl:apply-templates mode="metadata"/>
  </xsl:template>


  <xsl:template match="abbrev-journal-title" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Abbreviated Title</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <!-- trans-title-group content: (trans-title, trans-subtitle*) -->

  <xsl:template match="trans-title" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Translated Title</xsl:text>
        <xsl:for-each select="@xml:lang">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="trans-subtitle" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Translated Subtitle</xsl:text>
        <xsl:for-each select="@xml:lang">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <!-- article-meta content:
    (article-id*, article-categories?, title-group,
     (contrib-group | aff)*, author-notes?, pub-date+, volume?,
     volume-id*, volume-series?, issue?, issue-id*, 
     issue-title*, issue-sponsor*, issue-part?, isbn*, 
     supplement?, ((fpage, lpage?, page-range?) | elocation-id)?, 
     (email | ext-link | uri | product | supplementary-material)*, 
     history?, permissions?, self-uri*, related-article*,
     abstract*, trans-abstract*, 
     kwd-group*, funding-group*, conference*, counts?, 
     custom-meta-group?) -->

  <!-- In order of appearance... -->

  <xsl:template match="ext-link" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>External link</xsl:text>
        <xsl:for-each select="ext-link-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="."/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="email" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Email</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="."/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="uri" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">URI</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="."/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="self-uri" mode="metadata">
    <xsl:variable name="theurl" select="."/>
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Self URI</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <a href="{$theurl}">
          <xsl:choose>
            <xsl:when test="normalize-space()">
              <xsl:apply-templates/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="@xlink:href"/>
            </xsl:otherwise>
          </xsl:choose>
        </a>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="product" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Product Information</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:choose>
          <xsl:when test="normalize-space(@xlink:href)">
            <a>
              <xsl:call-template name="assign-href"/>
              <xsl:apply-templates/>
            </a>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="permissions" mode="metadata">
    <xsl:apply-templates select="copyright-statement" mode="metadata"/>
    <xsl:if test="copyright-year | copyright-holder">
      <xsl:call-template name="metadata-labeled-entry">
        <xsl:with-param name="label">Copyright</xsl:with-param>
        <xsl:with-param name="contents">
          <xsl:for-each select="copyright-year | copyright-holder">
            <xsl:apply-templates/>
            <xsl:if test="not(position()=last())">, </xsl:if>
          </xsl:for-each>
        </xsl:with-param>
      </xsl:call-template>
    </xsl:if>
    <xsl:apply-templates select="license" mode="metadata"/>
  </xsl:template>


  <xsl:template match="copyright-statement" mode="metadata">
    <p class="metadata-entry">
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="license" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">
        <xsl:text>License</xsl:text>
        <xsl:if test="@license-type | @xlink:href">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="@license-type"/>
            <xsl:if test="@xlink:href">
              <xsl:if test="@license-type">, </xsl:if>
              <a>
                <xsl:call-template name="assign-href"/>
                <xsl:value-of select="@xlink:href"/>
              </a>
            </xsl:if>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:if>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="history/date" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
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


  <xsl:template match="pub-date" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Publication date</xsl:text>
        <xsl:call-template name="append-pub-type"/>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:call-template name="format-date"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template name="volume-info">
    <!-- handles volume?, volume-id*, volume-series? -->
    <xsl:if test="volume | volume-id | volume-series">
      <xsl:choose>
        <xsl:when test="not(volume-id[2]) or not(volume)">
          <!-- if there are no multiple volume-id, or no volume, we make one line only -->
          <xsl:call-template name="metadata-labeled-entry">
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


  <xsl:template match="volume | issue" mode="metadata-inline">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="volume-id | issue-id" mode="metadata-inline">
    <span class="generated">
      <xsl:text> (</xsl:text>
      <xsl:for-each select="@pub-id-type">
        <span class="data">
          <xsl:value-of select="."/>
        </span>
        <xsl:text> </xsl:text>
      </xsl:for-each>
      <xsl:text>ID: </xsl:text>
    </span>
    <xsl:apply-templates/>
    <span class="generated">)</span>
  </xsl:template>


  <xsl:template match="volume-series" mode="metadata-inline">
    <xsl:if test="preceding-sibling::volume">
      <span class="generated">,</span>
    </xsl:if>
    <xsl:text> </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="volume" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Volume</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="volume-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Volume ID</xsl:text>
        <xsl:for-each select="@pub-id-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="volume-series" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Series</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template name="issue-info">
    <!-- handles issue?, issue-id*, issue-title*, issue-sponsor*, issue-part?, supplement? -->
    <xsl:variable name="issue-info"
      select="issue | issue-id | issue-title |
      issue-sponsor | issue-part"/>
    <xsl:choose>
      <xsl:when
        test="$issue-info and not(issue-id[2] | issue-title[2] | issue-sponsor | issue-part)">
        <!-- if there are only one issue, issue-id and issue-title and nothing else, we make one line only -->
        <xsl:call-template name="metadata-labeled-entry">
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


  <xsl:template match="issue-title" mode="metadata-inline">
    <span class="generated">
      <xsl:if test="preceding-sibling::issue">,</xsl:if>
    </span>
    <xsl:text> </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="issue" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Issue</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="issue-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Issue ID</xsl:text>
        <xsl:for-each select="@pub-id-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="issue-title" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Issue title</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="issue-sponsor" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Issue sponsor</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="issue-part" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Issue part</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template name="page-info">
    <!-- handles (fpage, lpage?, page-range?) -->
    <xsl:if test="fpage | lpage | page-range">
      <xsl:call-template name="metadata-labeled-entry">
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


  <xsl:template match="elocation-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Electronic Location
      Identifier</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <!-- isbn is already matched in mode 'metadata' above -->

  <xsl:template match="supplement" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Supplement Info</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="related-article | related-object" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Related </xsl:text>
          <xsl:choose>
            <xsl:when test="self::related-object">object</xsl:when>
            <xsl:otherwise>article</xsl:otherwise>
          </xsl:choose>
        <xsl:for-each select="@related-article-type | @object-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="translate(.,'-',' ')"/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:choose>
          <xsl:when test="normalize-space(@xlink:href)">
            <a>
              <xsl:call-template name="assign-href"/>
              <xsl:apply-templates/>
            </a>
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
        <xsl:call-template name="metadata-labeled-entry">
          <xsl:with-param name="label">Conference</xsl:with-param>
          <xsl:with-param name="contents">
            <xsl:apply-templates select="conf-acronym | conf-name"
              mode="metadata-inline"/>
            <xsl:apply-templates select="conf-num" mode="metadata-inline"/>
            <xsl:if test="conf-date | conf-loc">
              <span class="generated"> (</span>
              <xsl:for-each select="conf-date | conf-loc">
                <xsl:if test="position() = 2">, </xsl:if>
                <xsl:apply-templates select="." mode="metadata-inline"/>
              </xsl:for-each>
              <span class="generated">)</span>
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
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference date</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-name" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-acronym" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-num" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference number</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-loc" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference location</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-sponsor" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference sponsor</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-theme" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Conference theme</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="conf-name | conf-acronym" mode="metadata-inline">
    <!-- we only hit this template if there is at most one of each -->
    <xsl:variable name="following"
      select="preceding-sibling::conf-name | preceding-sibling::conf-acronym"/>
    <!-- if we come after the other, we go in parentheses -->
    <xsl:if test="$following">
      <span class="generated"> (</span>
    </xsl:if>
    <xsl:apply-templates/>
    <xsl:if test="$following">
      <span class="generated">)</span>
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
    <xsl:call-template name="metadata-labeled-entry">
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
          <xsl:when test="@pub-id-type='sici'">Serial Item and Contribution ID</xsl:when>
          <xsl:when test="@pub-id-type='doaj'">DOAJ ID</xsl:when>
          <xsl:otherwise>
            <xsl:text>Article Id</xsl:text>
            <xsl:for-each select="@pub-id-type">
              <xsl:text> (</xsl:text>
              <span class="data">
                <xsl:value-of select="."/>
              </span>
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
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Funded by</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="award-id" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Award ID</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="principal-award-recipient" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Award Recipient</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="principal-investigator" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Principal Investigator</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="funding-statement" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Funding</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="open-access" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Open Access</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="title-group" mode="metadata">
    <!-- content model:
    article-title, subtitle*, trans-title-group*, alt-title*, fn-group? -->
    <xsl:apply-templates select="article-title | subtitle | trans-title-group"
      mode="metadata"/>
    <xsl:if test="alt-title | fn-group">
      <div class="document-title-notes metadata-group">
        <xsl:apply-templates select="alt-title | fn-group" mode="metadata"/>
      </div>
    </xsl:if>
  </xsl:template>


  <xsl:template match="title-group/article-title" mode="metadata">
    <h1 class="document-title">
      <xsl:apply-templates/>
      <xsl:if test="../subtitle">:</xsl:if>
    </h1>
  </xsl:template>


  <xsl:template match="title-group/subtitle | trans-title-group/subtitle"
    mode="metadata">
    <h2 class="document-title">
      <xsl:apply-templates/>
    </h2>
  </xsl:template>


  <xsl:template match="title-group/trans-title-group" mode="metadata">
    <!-- content model: (trans-title, trans-subtitle*) -->
    <h3 class="document-title">
      <xsl:apply-templates mode="metadata"/>
    </h3>
  </xsl:template>


  <xsl:template match="trans-title-group/trans-title" mode="metadata">
    <span class="generated">
      <xsl:text>Translated title</xsl:text>
      <xsl:for-each select="(../@xml:lang | @xml:lang)[1]">
        <xsl:text> (</xsl:text>
        <xsl:value-of select="."/>
        <xsl:text>)</xsl:text>
      </xsl:for-each>
      <xsl:text>: </xsl:text>
    </span>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="title-group/alt-title" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Alternative title</xsl:text>
        <xsl:for-each select="@alt-title-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="title-group/fn-group" mode="metadata">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template mode="metadata" match="contrib-group">
      <!-- content model of contrib-group:
        (contrib+, 
        (address | aff | author-comment | bio | email |
        ext-link | on-behalf-of | role | uri | xref)*) -->
      <!-- each contrib makes a row: name at left, details at right -->
      <xsl:for-each select="contrib">
        <!-- content model of contrib: 
          ((anonymous | collab | name)*, (degrees)*, 
           (address | aff | author-comment | bio | email |
            ext-link | on-behalf-of | role | uri | xref)*) -->

            <xsl:call-template name="contrib-identify">
              <!-- handles
                   (anonymous | collab | name | degrees | xref) -->
            </xsl:call-template>

            <xsl:call-template name="contrib-info">
              <!-- handles
                   (address | aff | author-comment | bio | email |
                    ext-link | on-behalf-of | role | uri) -->
            </xsl:call-template>

      </xsl:for-each>
      <!-- end of contrib -->
      <xsl:variable name="misc-contrib-data"
        select="*[not(self::contrib | self::xref)]"/>
      <xsl:if test="$misc-contrib-data">

            <div class="metadata-group">
              <xsl:apply-templates mode="metadata"
                select="$misc-contrib-data"/>
            </div>

      </xsl:if>
  </xsl:template>


  <xsl:template name="contrib-identify">
    <!-- Placed in a left-hand pane  -->
    <div class="metadata-group">
      <xsl:apply-templates mode="metadata"
        select="anonymous | collab | name"/>
      <!-- degrees | xref will be handled along with the last
           of these children by the contrib-amend template -->
    </div>
  </xsl:template>


  <xsl:template match="anonymous" mode="metadata">
    <xsl:call-template name="metadata-entry">
      <xsl:with-param name="contents">
        <xsl:for-each
          select="self::*[not(preceding-sibling::*)]/parent::contrib">
          <!-- mark with an anchor for the parent contrib if this
               element is first -->
          <xsl:call-template name="named-anchor"/>
        </xsl:for-each>
        <xsl:text>Anonymous</xsl:text>
        <xsl:call-template name="contrib-amend">
          <xsl:with-param name="last-contrib"
            select="not(../following-sibling::contrib)"/>
            <!-- passes Boolean false if we are inside the last
                 contrib -->
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="collab" mode="metadata">
    <xsl:call-template name="metadata-entry">
      <xsl:with-param name="contents">
        <xsl:for-each
          select="self::*[not(preceding-sibling::*)]/parent::contrib">
          <!-- mark with an anchor for the parent contrib if this
               element is first -->
          <xsl:call-template name="named-anchor"/>
        </xsl:for-each>
        <xsl:choose>
        	<xsl:when test="contrib-group">
        		<xsl:apply-templates select="text()"/>
        		<xsl:apply-templates select="contrib-group" mode="metadata"/>
        	</xsl:when>
        	<xsl:otherwise>
        		<xsl:apply-templates/>
        	</xsl:otherwise>
        </xsl:choose>
        <xsl:call-template name="contrib-amend">
          <xsl:with-param name="last-contrib"
            select="not(../following-sibling::contrib)"/>
            <!-- passes Boolean false if we are inside the last
                 contrib -->
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="contrib/name" mode="metadata">
    <xsl:call-template name="metadata-entry">
      <xsl:with-param name="contents">
        <xsl:for-each
          select="self::*[not(preceding-sibling::*)]/parent::contrib">
          <!-- mark with an anchor for the parent contrib if this 
               element is first -->
          <xsl:call-template name="named-anchor"/>
        </xsl:for-each>
        <!-- (surname, given-names?, prefix?, suffix?) -->
        <xsl:call-template name="write-name"/>
        <xsl:call-template name="contrib-amend">
          <xsl:with-param name="last-contrib"
            select="not(../following-sibling::contrib)"/>
            <!-- passes Boolean false if we are inside the last
                 contrib -->
        </xsl:call-template>
      </xsl:with-param>
    </xsl:call-template>
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
      <xsl:apply-templates mode="metadata-inline"
        select="../degrees | ../xref"/>
      <xsl:if test="$last-contrib">
        <xsl:apply-templates mode="metadata-inline"
          select="parent::contrib/following-sibling::xref"/>
      </xsl:if>
    </xsl:if>
  </xsl:template>


  <xsl:template match="degrees" mode="metadata-inline">
    <xsl:text>, </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="xref" mode="metadata-inline">
    <xsl:apply-templates select="."/>
  </xsl:template>


  <xsl:template name="contrib-info">
    <!-- Placed in a right-hand pane -->
    <div class="metadata-group">
      <xsl:apply-templates mode="metadata"
        select="address | aff | author-comment | bio | email |
                ext-link | on-behalf-of | role | uri"/>
    </div>
  </xsl:template>


  <xsl:template mode="metadata"
    match="address[not(addr-line) or not(*[2])]">
    <!-- when we have no addr-line or a single child, we generate
         a single unlabelled line -->
        <xsl:call-template name="metadata-entry">
          <xsl:with-param name="contents">
            <xsl:call-template name="address-line"/>
          </xsl:with-param>
        </xsl:call-template>
  </xsl:template>


  <xsl:template match="address" mode="metadata">
    <!-- when we have an addr-line we generate an unlabelled block -->
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template mode="metadata" priority="2" match="address/*">
    <!-- being sure to override other templates for these
         element types -->
    <xsl:call-template name="metadata-entry"/>
  </xsl:template>


  <xsl:template match="aff" mode="metadata">
    <xsl:call-template name="metadata-entry">
      <xsl:with-param name="contents">
        <xsl:call-template name="named-anchor"/>
        <xsl:apply-templates/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="author-comment" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Comment</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="bio" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Bio</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="on-behalf-of" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">On behalf of</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="role" mode="metadata">
    <xsl:call-template name="metadata-entry"/>
  </xsl:template>


  <xsl:template match="author-notes" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Author notes</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:call-template name="named-anchor"/>
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="author-notes/corresp" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:call-template name="named-anchor"/>
        <xsl:text>Correspondence to</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="author-notes/fn | author-notes/p" mode="metadata">
    <xsl:call-template name="metadata-entry">
      <xsl:with-param name="contents">
        <xsl:call-template name="named-anchor"/>
        <xsl:apply-templates/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="supplementary-material" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Supplementary material</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="article-categories" mode="metadata">
    <xsl:apply-templates mode="metadata"/>
  </xsl:template>


  <xsl:template match="article-categories/subj-group" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Categories</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="subj-group" mode="metadata">
    <xsl:apply-templates mode="metadata"/>
  </xsl:template>


  <xsl:template match="subj-group/subj-group" mode="metadata">
    <div class="metadata-area">
      <xsl:apply-templates mode="metadata"/>
    </div>
  </xsl:template>


  <xsl:template match="subj-group/subject" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Subject</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="series-title" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Series title</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="series-text" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Series description</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="kwd-group" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">
        <xsl:apply-templates select="title|label" mode="metadata-inline"/>
        <xsl:if test="not(title|label)">Keywords</xsl:if>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="title" mode="metadata">
    <xsl:apply-templates select="."/>
  </xsl:template>


  <xsl:template match="kwd" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">Keyword</xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="compound-kwd" mode="metadata">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Compound keyword</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="compound-kwd-part" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:text>Keyword part</xsl:text>
        <xsl:for-each select="@content-type">
          <xsl:text> (</xsl:text>
          <span class="data">
            <xsl:value-of select="."/>
          </span>
          <xsl:text>)</xsl:text>
        </xsl:for-each>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="counts" mode="metadata">
    <!-- fig-count?, table-count?, equation-count?, ref-count?,
         page-count?, word-count? -->
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Counts</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template mode="metadata"
    match="fig-count | table-count | equation-count |
           ref-count | page-count | word-count">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <xsl:apply-templates select="." mode="metadata-label"/>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:value-of select="@count"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="table-count"
    mode="metadata-label">Figures</xsl:template>


  <xsl:template match="table-count"
    mode="metadata-label">Tables</xsl:template>


  <xsl:template match="equation-count"
    mode="metadata-label">Equations</xsl:template>


  <xsl:template match="ref-count"
    mode="metadata-label">References</xsl:template>


  <xsl:template match="page-count"
    mode="metadata-label">Pages</xsl:template>


  <xsl:template match="word-count"
    mode="metadata-label">Words</xsl:template>


  <xsl:template mode="metadata"
    match="custom-meta-group">
    <xsl:call-template name="metadata-area">
      <xsl:with-param name="label">Custom metadata</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates mode="metadata"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="custom-meta" mode="metadata">
    <xsl:call-template name="metadata-labeled-entry">
      <xsl:with-param name="label">
        <span class="data">
          <xsl:apply-templates select="meta-name" mode="metadata-inline"/>
        </span>
      </xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="meta-value" mode="metadata-inline"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="meta-name | meta-value" mode="metadata-inline">
    <xsl:apply-templates/>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  REGULAR (DEFAULT) MODE                                       -->
  <!-- ============================================================= -->


  <xsl:template match="sec">
    <div class="section">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="title"/>
      <xsl:apply-templates select="sec-meta"/>
      <xsl:apply-templates mode="drop-title"/>
    </div>
  </xsl:template>


  <xsl:template match="*" mode="drop-title">
    <xsl:apply-templates select="."/>
  </xsl:template>


  <xsl:template match="title | sec-meta" mode="drop-title"/>


  <xsl:template match="app">
    <div class="section app">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  
  <xsl:template match="ref-list" name="ref-list">
    <div class="section ref-list">
      <!--<xsl:call-template name="named-anchor"/>-->
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates select="*[not(self::ref | self::ref-list)]"/>
      <xsl:if test="ref">
        <ul>
          <xsl:apply-templates select="ref"/>
        </ul>
      </xsl:if>
      <xsl:apply-templates select="ref-list"/>
      
    </div>
  </xsl:template>
  
  
  <xsl:template match="sec-meta">
   <div class="section-metadata">
     <!-- includes contrib-group | permissions | kwd-group -->
     <xsl:apply-templates/>
   </div>
  </xsl:template>


  <xsl:template match="sec-meta/contrib-group">
    <xsl:apply-templates mode="metadata"/>
  </xsl:template>


  <xsl:template match="sec-meta/kwd-group">
    <!-- matches only if contrib-group has only contrib children -->
    <xsl:apply-templates  select="." mode="metadata"/>
  </xsl:template>



  <!-- ============================================================= -->
  <!--  Titles                                                       -->
  <!-- ============================================================= -->

  <xsl:template name="main-title"
    match="abstract/title | body/*/title |
           back/title | back[not(title)]/*/title">
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <xsl:if test="normalize-space($contents)">
      <!-- coding defensively since empty titles make glitchy HTML -->
      <h2 class="main-title">
        <xsl:copy-of select="$contents"/>
      </h2>
    </xsl:if>
  </xsl:template>


  <xsl:template name="section-title"
    match="abstract/*/title | body/*/*/title |
		       back[title]/*/title | back[not(title)]/*/*/title">
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>   
    <xsl:if test="normalize-space($contents)">
      <!-- coding defensively since empty titles make glitchy HTML -->
      <h3 class="section-title">
        <xsl:copy-of select="$contents"/>
      </h3>
    </xsl:if>
  </xsl:template>


  <xsl:template name="subsection-title"
    match="abstract/*/*/title | body/*/*/*/title |
		       back[title]/*/*/title | back[not(title)]/*/*/*/title">
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>   
    <xsl:if test="normalize-space($contents)">
      <!-- coding defensively since empty titles make glitchy HTML -->
      <h4 class="subsection-title">
        <xsl:copy-of select="$contents"/>
      </h4>
    </xsl:if>
  </xsl:template>


  <xsl:template name="block-title" priority="2"
    match="list/title | def-list/title | boxed-text/title |
           verse-group/title | glossary/title | kwd-group/title">
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>   
    <xsl:if test="normalize-space($contents)">
      <!-- coding defensively since empty titles make glitchy HTML -->
      <h4 class="block-title">
        <xsl:copy-of select="$contents"/>
      </h4>
    </xsl:if>
  </xsl:template>


  <!-- default: any other titles found -->
  <xsl:template match="title">
    <xsl:if test="normalize-space()">
      <h3 class="title">
        <xsl:apply-templates/>
      </h3>
    </xsl:if>
  </xsl:template>


  <xsl:template match="subtitle">
    <xsl:if test="normalize-space()">
      <h5 class="subtitle">
        <xsl:apply-templates/>
      </h5>
    </xsl:if>
  </xsl:template>


<!-- ============================================================= -->
<!--  Figures, lists and block-level objectS                       -->
<!-- ============================================================= -->
  
  
  <xsl:template match="address">
    <xsl:choose>
      <!-- address appears as a sequence of inline elements if
           it has no addr-line and the parent may contain text -->
      <xsl:when test="not(addr-line) and
        (parent::collab | parent::p | parent::license-p |
         parent::named-content | parent::styled-content)">
        <xsl:call-template name="address-line"/>
      </xsl:when>
      <xsl:otherwise>
        <div class="address">
          <xsl:apply-templates/>
        </div>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template name="address-line">
    <!-- emits element children in a simple comma-delimited sequence -->
    <xsl:for-each select="*">
      <xsl:if test="position() &gt; 1">, </xsl:if>
      <xsl:apply-templates/>
    </xsl:for-each>
  </xsl:template>


  <xsl:template match="address/*">
    <p class="address-line">
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="alternatives">
    <xsl:apply-templates/>
  </xsl:template>
  
  
  <xsl:template match="array | disp-formula-group | fig-group |
    fn-group | license | long-desc | open-access | sig-block | 
    table-wrap-foot | table-wrap-group">
    <div class="{local-name()}">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  
  <xsl:template match="attrib">
    <p class="attrib">
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="boxed-text | chem-struct-wrap | fig |
                       table-wrap">
    <div class="{local-name()} panel">
      <xsl:if test="not(@position != 'float')">
        <!-- the test respects @position='float' as the default -->
        <xsl:attribute name="style">display: float; clear: both</xsl:attribute>
      </xsl:if>
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates/>
      <xsl:apply-templates mode="footnote"
        select="self::table-wrap//fn[not(ancestor::table-wrap-foot)]"/>
    </div>
  </xsl:template>
  

  <xsl:template match="caption">
    <div class="caption">
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  

  <xsl:template match="disp-formula | statement">
    <div class="{local-name()} panel">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  

  <xsl:template match="glossary">
    <div class="glossary">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="label | title"/>
      <xsl:if test="not(normalize-space(title))">
        <xsl:call-template name="block-title">
          <xsl:with-param name="contents">
            <span class="generated">Glossary</span>
          </xsl:with-param>
        </xsl:call-template>
      </xsl:if>
      <xsl:apply-templates select="*[not(self::label|self::title)]"/>
    </div>
  </xsl:template>
  

  <xsl:template match="textual-form">
    <p class="textual-form">
      <span class="generated">[Textual form] </span>
      <xsl:apply-templates/>
    </p>
  </xsl:template>
  


  <xsl:template match="glossary/glossary">
    <div class="glossary">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  


  <xsl:template match="graphic | inline-graphic">
    <xsl:apply-templates/>
    <a href="{@xlink:href}" rel="lightbox"><img class="inline-graphic" alt="{@xlink:href}">
      <xsl:for-each select="alt-text">
        <xsl:attribute name="alt">
          <xsl:value-of select="normalize-space(.)"/>
        </xsl:attribute>
      </xsl:for-each>
      <xsl:call-template name="assign-src"/>
    </img></a>
  </xsl:template>
  
  
  <xsl:template match="alt-text">
    <!-- handled with graphic or inline-graphic -->
  </xsl:template>
  

  <xsl:template match="list">
    <div class="list">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="label | title"/>
      <xsl:apply-templates select="." mode="list"/>
    </div>
  </xsl:template>
  

  <xsl:template priority="2" mode="list"
    match="list[@list-type='simple' or list-item/label]">
    <ul style="list-style-type: none">
      <xsl:apply-templates select="list-item"/>
    </ul>
  </xsl:template>


  <xsl:template match="list[@list-type='bullet' or not(@list-type)]" mode="list">
    <ul>
      <xsl:apply-templates select="list-item"/>
    </ul>
  </xsl:template>


  <xsl:template match="list" mode="list">
    <xsl:variable name="style">
      <xsl:choose>
        <xsl:when test="@list-type='alpha-lower'">lower-alpha</xsl:when>
        <xsl:when test="@list-type='alpha-upper'">upper-alpha</xsl:when>
        <xsl:when test="@list-type='roman-lower'">lower-roman</xsl:when>
        <xsl:when test="@list-type='roman-upper'">upper-roman</xsl:when>
        <xsl:otherwise>decimal</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <ol style="list-style-type: {$style}">
      <xsl:apply-templates select="list-item"/>
    </ol>
  </xsl:template>
  

	<xsl:template match="list-item">
		<li>
			<xsl:apply-templates/>
		</li>
	</xsl:template>


	<xsl:template match="list-item/label">
	  <!-- if the next sibling is a p, the label will be called as
	       a run-in -->
	  <xsl:if test="following-sibling::*[1][not(self::p)]">
	    <xsl:call-template name="label"/>
	  </xsl:if>
	</xsl:template>
  
  
	<xsl:template match="media">
		<a>
			<xsl:call-template name="assign-id"/>
			<xsl:call-template name="assign-href"/>
			<xsl:apply-templates/>
		</a>
	</xsl:template>


  <xsl:template match="p | license-p">
    <p>
      <xsl:if test="not(preceding-sibling::*)">
        <xsl:attribute name="class">first</xsl:attribute>
      </xsl:if>
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates select="@content-type"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>
  
  
  <xsl:template match="@content-type">
    <!-- <span class="generated">[</span>
    <xsl:value-of select="."/>
    <span class="generated">] </span> -->
  </xsl:template>


  <xsl:template match="list-item/p[not(preceding-sibling::*[not(self::label)])]">
    <p>
      <xsl:call-template name="assign-id"/>
      <xsl:for-each select="preceding-sibling::label">
        <span class="label">
          <xsl:apply-templates/>
        </span>
      <xsl:text> </xsl:text>
      </xsl:for-each>
      <xsl:apply-templates select="@content-type"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="product">
    <p class="product">
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="permissions">
    <div class="permissions">
    <xsl:apply-templates select="copyright-statement"/>
    <xsl:if test="copyright-year | copyright-holder">
      <p class="copyright">
        <span class="generated">Copyright</span>
        <xsl:for-each select="copyright-year | copyright-holder">
            <xsl:apply-templates/>
            <xsl:if test="not(position()=last())">
              <span class="generated">, </span>
            </xsl:if>
        </xsl:for-each>
      </p>
    </xsl:if>
    <xsl:apply-templates select="license"/>
    </div>
  </xsl:template>
  
  
  <xsl:template match="copyright-statement">
    <p class="copyright">
      <xsl:apply-templates></xsl:apply-templates>
    </p>
  </xsl:template>


  <xsl:template match="def-list">
    <div class="def-list">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="label | title"/>
      <table class="def-list">
        <xsl:if test="term-head|def-head">
          <tr>
            <th class="def-list-head">
              <xsl:apply-templates select="term-head"/>
            </th>
            <th class="def-list-head">
              <xsl:apply-templates select="def-head"/>
            </th>
          </tr>
        </xsl:if>
        <xsl:apply-templates select="def-item"/>
      </table>
      <xsl:apply-templates select="def-list"/>
    </div>
  </xsl:template>


	<xsl:template match="def-item">
		<tr>
			<xsl:call-template name="assign-id"/>
			<xsl:apply-templates/>
		</tr>
	</xsl:template>


	<xsl:template match="term">
		<td class="def-term">
			<xsl:call-template name="assign-id"/>
		  <p>
				<xsl:apply-templates/>
		  </p>
		</td>
	</xsl:template>


	<xsl:template match="def">
		<td valign="def-def">
			<xsl:call-template name="assign-id"/>
			<xsl:apply-templates/>
		</td>
	</xsl:template>

  <xsl:template match="pnoindent">
    <p>
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  <xsl:template match="disp-quote">
    <div class="blockquote">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>


  <xsl:template match="preformat">
    <pre class="preformat">
      <xsl:apply-templates/>
    </pre>
  </xsl:template>


  <xsl:template match="ref">
        <li class="ref-content">
          <xsl:apply-templates/>
        </li>
  </xsl:template>
    
  
  <xsl:template match="ref/*" priority="0">
    <!-- should match mixed-citation, element-citation, nlm-citation.
         note and label should be matched below. -->
    <!--<p class="citation">-->
    
      <!--<xsl:call-template name="named-anchor"/>-->
      <xsl:apply-templates/>
    
    <!--</p>-->
  </xsl:template>
 
 
  <xsl:template match="ref/note" priority="2">
    <xsl:param name="label" select="''"/>
    <xsl:if test="normalize-space($label) and not(preceding-sibling::*[not(self::label)])">
      <p class="label">
          <xsl:copy-of select="$label"/>
      </p>
    </xsl:if>
    <div class="note">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  
  <xsl:template match="app/related-article |
    app-group/related-article | bio/related-article | 
    body/related-article | boxed-text/related-article | 
    disp-quote/related-article | glossary/related-article |
    ref-list/related-article | sec/related-article">
    <xsl:apply-templates select="." mode="metadata"/>
  </xsl:template>
  
  
  <xsl:template match="app/related-object |
    app-group/related-object | bio/related-object |
    body/related-object | boxed-text/related-object | 
    disp-quote/related-object | glossary/related-object |
    ref-list/related-object | sec/related-object">
    <xsl:apply-templates select="." mode="metadata"/>
  </xsl:template>
  
  
  <xsl:template match="speech">
    <div class="speech">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates mode="speech"/>
    </div>
  </xsl:template>
  
  
  <xsl:template match="speech/speaker" mode="speech"/>
    
    
  <xsl:template match="speech/p" mode="speech">
    <p>
      <xsl:apply-templates select="self::p[not(preceding-sibling::p)]/../speaker"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>
  
  
  <xsl:template match="speech/speaker">
    <b>
      <xsl:apply-templates/>
    </b>
    <span class="generated">: </span>
  </xsl:template>
  
  
  <xsl:template match="supplementary-material">
    <div class="panel">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates select="." mode="label"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  

	<xsl:template match="tex-math">
		<span class="tex-math">
			<span class="generated">[TeX:] </span>
			<xsl:apply-templates/>
		</span>
	</xsl:template>

  
  <xsl:template match="mml:*">
    <!-- this stylesheet simply copies MathML through. If your browser
         supports it, you will get it -->
    <xsl:copy>
      <xsl:copy-of select="@*"/>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>
  
  
  <xsl:template match="verse-group">
    <div class="verse">
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>
  
  
  <xsl:template match="verse-line">
    <p class="verse-line">
      <xsl:apply-templates/>
    </p>
  </xsl:template>
  
  
  <xsl:template match="aff/label | corresp/label |
    chem-struct/label | element-citation/label | mixed-citation/label">
    <!-- these labels appear in line -->
    <span class="generated">[</span>
    <xsl:apply-templates/>
    <span class="generated">] </span>
  </xsl:template>


  <xsl:template match="app/label | boxed-text/label | chem-struct-wrap/label |
    disp-formula/label | fig/label | fn/label | ref/label |
    statement/label | supplementary-material/label | table-wrap/label"
    priority="2">
    <!-- suppressed, since acquired by their parents in mode="label" -->
  </xsl:template>


  <xsl:template match="label" name="label">
    <!-- other labels are displayed as blocks -->
    <h5 class="label">
      <xsl:apply-templates/>
    </h5>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  TABLES                                                       -->
  <!-- ============================================================= -->
  <!--  Tables are already in XHTML, and can simply be copied
        through                                                      -->
  
  
  <xsl:template match="table | thead | tbody | tfoot |
      col | colgroup | tr | th | td">
    <xsl:copy>
      <xsl:apply-templates select="@*" mode="table-copy"/>
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </xsl:copy>
  </xsl:template>
  
  
  <xsl:template match="array/tbody">
    <table>
      <xsl:copy>
      <xsl:apply-templates select="@*" mode="table-copy"/>
      <xsl:call-template name="named-anchor"/>
      <xsl:apply-templates/>
    </xsl:copy>
    </table>
  </xsl:template>
  
  
  <xsl:template match="@*" mode="table-copy">
    <xsl:copy-of select="."/>
  </xsl:template>
  
  
  <xsl:template match="@content-type" mode="table-copy"/>
  
  
  <!-- ============================================================= -->
  <!--  INLINE MISCELLANEOUS                                         -->
  <!-- ============================================================= -->
  <!--  Templates strictly for formatting follow; these are templates
        to handle various inline structures -->


  <xsl:template match="abbrev">
    <xsl:apply-templates/>
  </xsl:template>
  
    
  <xsl:template match="abbrev/def">
    <xsl:text>[</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>]</xsl:text>
  </xsl:template>
  
  <xsl:template match="p/address | license-p/address |
    named-content/p | styled-content/p">
    <xsl:apply-templates mode="inline"/>
  </xsl:template>
  
  
  <xsl:template match="address/*" mode="inline">
    <xsl:if test="preceding-sibling::*">
      <span class="generated">, </span>
    </xsl:if>
    <xsl:apply-templates/>
  </xsl:template>
  
        
  <xsl:template match="award-id">
    <xsl:apply-templates/>
  </xsl:template>
  
    
  <xsl:template match="award-id[normalize-space(@rid)]">
    <a href="#{@rid}">
      <xsl:apply-templates/>
    </a>
  </xsl:template>
  
    
  <xsl:template match="break">
    <br class="br"/>
  </xsl:template>


  <xsl:template match="email">
    <a href="mailto:{.}">
      <xsl:apply-templates/>
    </a>
  </xsl:template>

  
  <xsl:template match="ext-link | uri | inline-supplementary-material">
    <a target="xrefwindow">
      <xsl:attribute name="href">
        <xsl:value-of select="."/>
      </xsl:attribute>
      <!-- if an @href is present, it overrides the href
           just attached -->
      <xsl:call-template name="assign-href"/>
      <xsl:call-template name="assign-id"/>
      <xsl:apply-templates/>
      <xsl:if test="not(normalize-space())">
        <xsl:value-of select="@xlink:href"/>
      </xsl:if>
    </a>
  </xsl:template>


  <xsl:template match="funding-source">
    <span class="funding-source">
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  

  <xsl:template match="hr">
    <hr></hr>
  </xsl:template>
  

  <!-- inline-graphic is handled above, with graphic -->
  
  
  <xsl:template match="inline-formula | chem-struct">
    <span class="{local-name()}">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="chem-struct-wrap/chem-struct">
    <div class="{local-name()}">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  
  <xsl:template match="milestone-start | milestone-end">
    <span class="{substring-after(local-name(),'milestone-')}">
      <xsl:comment>
        <xsl:value-of select="@rationale"/>
      </xsl:comment>
    </span>
  </xsl:template>
  

  <xsl:template match="object-id">
    <span class="{local-name()}">
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  

  <!-- preformat is handled above -->
  
  <xsl:template match="sig">
    <xsl:apply-templates/>
  </xsl:template>
  

  <xsl:template match="target">
    <xsl:call-template name="named-anchor"/>
  </xsl:template>
  
  
  <xsl:template match="styled-content">
    <span>
      <xsl:copy-of select="@style"/>
      <xsl:for-each select="@style-type">
        <xsl:attribute name="class">
          <xsl:value-of select="."/>
        </xsl:attribute>
      </xsl:for-each>
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  
  
  <xsl:template match="named-content">
    <span>
      <xsl:for-each select="@content-type">
        <xsl:attribute name="class">
          <xsl:value-of select="translate(.,' ','-')"/>
        </xsl:attribute>
      </xsl:for-each>
      <xsl:apply-templates/>
    </span>
  </xsl:template>
  
  
  <xsl:template match="private-char">
    <span>
      <xsl:for-each select="@description">
        <xsl:attribute name="title">
          <xsl:value-of select="."/>
        </xsl:attribute>
      </xsl:for-each>
      <span class="generated">[Private character </span>
      <xsl:for-each select="@name">
        <xsl:text> </xsl:text>
        <xsl:value-of select="."/>
      </xsl:for-each>
      <span class="generated">]</span>
    </span>
  </xsl:template>
  
  
  <xsl:template match="glyph-data | glyph-ref">
    <span class="generated">(Glyph not rendered)</span>
  </xsl:template>
    
  
  <xsl:template match="related-article">
    <span class="generated">[Related article:] </span>
    <xsl:apply-templates/>
  </xsl:template>
  
  
  <xsl:template match="related-object">
    <span class="generated">[Related object:] </span>
    <xsl:apply-templates/>
  </xsl:template>
  
  
  <xsl:template match="xref[not(normalize-space())]">
    <xsl:variable name="fn-number">
      <xsl:number level="any" count="xref[not(ancestor::front)]"
        from="article | sub-article | response"/>
    </xsl:variable>
  	<xsl:choose>
  		<xsl:when test="@ref-type='aff' and count(/article/front/article-meta//aff)=1"/>
  	  <xsl:when test="@ref-type='fn'">
  	    <!-- this is an auto-numbered footnote -->
  	    <a href="#fn{$fn-number}" id="xr{$fn-number}"><sup><xsl:copy-of select="$fn-number" /></sup>
  	      <xsl:apply-templates/>
  	    </a>
  	  </xsl:when>
  		<xsl:otherwise>
		    <a href="#{@rid}">
		      <xsl:apply-templates select="key('element-by-id',@rid)"
		        mode="label-text">
		        <xsl:with-param name="warning" select="true()"/>
		      </xsl:apply-templates>
		    </a>
  		</xsl:otherwise>
  	</xsl:choose>
  </xsl:template>


  <xsl:template match="xref">
    <xsl:variable name="fn-number">
      <xsl:number level="any" count="xref[not(ancestor::front)]"
        from="article | sub-article | response"/>
    </xsl:variable>
    <xsl:if test="@ref-type='fn'">
      <!-- this is an auto-numbered footnote -->
      <a href="#fn{$fn-number}" id="xr{$fn-number}"><sup><xsl:copy-of select="$fn-number" /></sup>
        <xsl:apply-templates/>
      </a>
    </xsl:if>
  </xsl:template>

<xsl:template match="fn-link">
    <a href="#{@href}" id="{@id}">
      <xsl:apply-templates/>
    </a> 
</xsl:template>

  
  <!-- ============================================================= -->
  <!--  Formatting elements                                          -->
  <!-- ============================================================= -->


  <xsl:template match="bold">
    <b>
      <xsl:apply-templates/>
    </b>
  </xsl:template>


  <xsl:template match="italic">
    <i>
      <xsl:apply-templates/>
    </i>
  </xsl:template>


  <xsl:template match="monospace">
    <tt>
      <xsl:apply-templates/>
    </tt>
  </xsl:template>


  <xsl:template match="overline">
    <span style="text-decoration: overline">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="price">
    <span class="price">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="roman">
    <span style="font-style: normal">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="sans-serif">
    <span style="font-family: sans-serif; font-size: 80%">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="sc">
    <span style="font-variant: small-caps">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="strike">
    <span style="text-decoration: line-through">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <xsl:template match="sub">
    <sub>
      <xsl:apply-templates/>
    </sub>
  </xsl:template>


  <xsl:template match="sup">
    <sup>
      <xsl:apply-templates/>
    </sup>
  </xsl:template>


  <xsl:template match="underline">
    <span style="text-decoration: underline">
      <xsl:apply-templates/>
    </span>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  BACK MATTER                                                  -->
  <!-- ============================================================= -->


  <xsl:variable name="loose-footnotes"
    select="//fn[not(ancestor::front|parent::fn-group|ancestor::table-wrap)]"/>
    
    
  <xsl:template name="make-back">
    <xsl:apply-templates select="back"/>
    <xsl:if test="$loose-footnotes and not(back)">
      <!-- autogenerating a section for footnotes only if there is no
           back element, and if footnotes exist for it -->
      <xsl:call-template name="footnotes"/>
    </xsl:if>
  </xsl:template>
    
  <xsl:template match="back">
    <!-- content model for back: 
          (label?, title*, 
          (ack | app-group | bio | fn-group | glossary | ref-list |
           notes | sec)*) -->
    <xsl:if test="not(fn-group) and $loose-footnotes">
      <xsl:call-template name="footnotes"/>
    </xsl:if>
    <xsl:apply-templates/>
  </xsl:template>
  
  
  <xsl:template name="footnotes">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Notes</xsl:with-param>
      <xsl:with-param name="contents">
        <xsl:apply-templates select="$loose-footnotes" mode="footnote"/>
      </xsl:with-param>
    </xsl:call-template>
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
  

  <xsl:template match="back/bio">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Biography</xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  

  <xsl:template match="back/fn-group">
    <xsl:call-template name="backmatter-section">
      <xsl:with-param name="generated-title">Notes</xsl:with-param>
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
        <xsl:call-template name="ref-list"/>
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
    <div class="back-section">
      <xsl:call-template name="named-anchor"/>
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
    </div>
  </xsl:template>
  

  

  <!-- ============================================================= -->
  <!--  FOOTNOTES                                                    -->
  <!-- ============================================================= -->

  <xsl:template match="fn">
  <!-- Footnotes appearing outside fn-group
       generate cross-references to the footnote,
       which is displayed elsewhere -->
  <!-- Note the rules for displayed content: if any fn elements
       not inside an fn-group (the matched fn or any other) includes
       a label child, all footnotes are expected to have a label
       child. -->
    <xsl:variable name="id">
      <xsl:apply-templates select="." mode="id"/>
    </xsl:variable>
    <a href="#{$id}">
      <xsl:apply-templates select="." mode="label-text">
        <xsl:with-param name="warning" select="true()"/>
      </xsl:apply-templates>
    </a>
  </xsl:template>
  
  <xsl:template match="fn-group/fn | table-wrap-foot/fn |
                       table-wrap-foot/fn-group/fn">
    <xsl:apply-templates select="." mode="footnote"/>
  </xsl:template>
  
  
  <xsl:template match="fn" mode="footnote">
    <div class="footnote">
      <!--<xsl:call-template name="named-anchor"/>-->
      <xsl:apply-templates />
    </div>
  </xsl:template>
  
  
  <xsl:template match="fn/p">
    <p>
      <xsl:call-template name="assign-id"/>
      <xsl:if test="not(preceding-sibling::p)">
        <xsl:apply-templates select="parent::fn" mode="label-text"/>
        <xsl:text> </xsl:text>
      </xsl:if>
      <xsl:apply-templates/>
    </p>
  </xsl:template>


  
  
  <!-- ============================================================= -->
  <!--  MODE 'label-text'
	      Generates label text for elements and their cross-references -->
  <!-- ============================================================= -->
  <!--  This mode is to support auto-numbering and generating of
        labels for certain elements by the stylesheet.
  
        The logic is as follows: for any such element type, if a
        'label' element is ever present, it is expected always to be 
        present; automatic numbering is not performed on any elements
        of that type. For example, the presence of a 'label' element 
        in any 'fig' is taken to indicate that all figs should likewise
        be labeled, and any 'fig' without a label is supposed to be 
        unlabelled (and unnumbered). But if no 'fig' elements have 
        'label' children, labels with numbers are generated for all 
        figs in display.
        
        This logic applies to:
          app, boxed-text, chem-struct-wrap, disp-formula, fig, fn, 
          note, ref, statement, table-wrap.
        
        There is one exception in the case of fn elements, where
        the checking for labels (or for @symbol attributes in the
        case of this element) is performed only within its parent
        fn-group, or in the scope of all fn elements not in an
        fn-group, for fn elements appearing outside fn-group.
        
        In all cases, this logic can be altered simply by overwriting 
        templates in "label" mode for any of these elements.
        
        For other elements, a label is simply displayed if present,
        and auto-numbering is never performed.
        These elements include:
          (label appearing in line) aff, corresp, chem-struct, 
          element-citation, mixed-citation
          
          (label appearing as a block) abstract, ack, app-group, 
          author-notes, back, bio, def-list, disp-formula-group, 
          disp-quote, fn-group, glossary, graphic, kwd-group, 
          list, list-item, media, notes, ref-list, sec, 
          supplementary-material, table-wrap-group, 
          trans-abstract, verse-group -->


  <xsl:variable name="auto-label-app" select="false()"/>
  <xsl:variable name="auto-label-boxed-text" select="false()"/>
  <xsl:variable name="auto-label-chem-struct-wrap" select="false()"/>
  <xsl:variable name="auto-label-disp-formula" select="false()"/>
  <xsl:variable name="auto-label-fig" select="false()"/>
  <xsl:variable name="auto-label-ref" select="not(//ref[label])"/>
  <!-- ref elements are labeled unless any ref already has a label -->
  
  <xsl:variable name="auto-label-statement" select="false()"/>
  <xsl:variable name="auto-label-supplementary"
    select="false()"/>
  <xsl:variable name="auto-label-table-wrap" select="false()"/>

<!--
  These variables assignments show how autolabeling can be 
  configured conditionally.
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
      <!-- not to create an h5 for nothing -->
      <h5 class="label">
        <xsl:copy-of select="$contents"/>
      </h5>
    </xsl:if>
  </xsl:template>


  <xsl:template mode="label" match="ref">
    <xsl:param name="contents">
      <xsl:apply-templates select="." mode="label-text"/>
    </xsl:param>
    <xsl:if test="normalize-space($contents)">
      <!-- we're already in a p -->
        <span class="label">
          <xsl:copy-of select="$contents"/>
        </span>
    </xsl:if>
  </xsl:template>

  
  <xsl:template match="app" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-app"/>
      <xsl:with-param name="warning" select="$warning"/>
      <!--
      Pass in the desired label if a label is to be autogenerated  
      <xsl:with-param name="auto-text">
        <xsl:text>Appendix </xsl:text>
        <xsl:number format="A"/>
      </xsl:with-param>-->
    </xsl:call-template>
  </xsl:template>
  

  <xsl:template match="boxed-text" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
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
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
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
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
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
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-fig"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>Figure </xsl:text>
        <xsl:number level="any"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="front//fn" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:variable name="auto-number-fn"
      select="not(ancestor::front//fn/label | ancestor::front//fn/@symbol)"/>
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-number-fn"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>[</xsl:text>
        <xsl:number level="any" count="fn" from="front" format="a"/>
        <xsl:text>]</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  
  
  <xsl:template match="table-wrap//fn" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:variable name="auto-number-fn"
      select="not(ancestor::table-wrap//fn/label | ancestor::table-wrap//fn/@symbol)"/>
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-number-fn"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>[</xsl:text>
        <xsl:number level="any" count="fn" from="table-wrap" format="i"/>
        <xsl:text>]</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  
  
  <xsl:template match="fn" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:variable name="auto-number-fn"
      select="not(ancestor::article//fn[not(ancestor::front|ancestor::table-wrap)]/label |
                  ancestor::article//fn[not(ancestor::front|ancestor::table-wrap)]/@symbol)"/>
    <xsl:variable name="fn-number">
      <xsl:number level="any" count="fn[not(ancestor::front)]"
        from="article | sub-article | response"/>
    </xsl:variable>
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-number-fn"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <a href="#xr{$fn-number}" id="fn{$fn-number}">
          <xsl:copy-of select="$fn-number" />
        </a>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template match="ref" mode="label-text">
    <xsl:param name="warning" select="true()"/>
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
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
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
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
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
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
    <!-- pass $warning in as false() if a warning string is not wanted
         (for example, if generating autonumbered labels) -->
    <xsl:call-template name="make-label-text">
      <xsl:with-param name="auto" select="$auto-label-table-wrap"/>
      <xsl:with-param name="warning" select="$warning"/>
      <xsl:with-param name="auto-text">
        <xsl:text>Table </xsl:text>
        <xsl:number level="any" format="I"/>
      </xsl:with-param>
    </xsl:call-template>
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
	<!-- originally: mode="inline-label-text" -->
  </xsl:template>
  
  
  <xsl:template match="text()" mode="inline-label-text">
    <!-- when displaying labels, space characters become non-breaking spaces -->
    <xsl:value-of select="translate(normalize-space(.),' &#xA;&#x9;','&#xA0;&#xA0;&#xA0;')"/>
  </xsl:template>
  

<!-- ============================================================= -->
<!--  Writing a name                                               -->
<!-- ============================================================= -->

  <!-- Called when displaying structured names in metadata         -->

  <xsl:template name="write-name" match="name">
    <xsl:apply-templates select="prefix" mode="inline-name"/>
    <xsl:apply-templates select="surname[../@name-style='eastern']"
      mode="inline-name"/>
    <xsl:apply-templates select="given-names" mode="inline-name"/>
    <xsl:apply-templates select="surname[not(../@name-style='eastern')]"
      mode="inline-name"/>
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
<!--  UTILITY TEMPLATES                                           -->
<!-- ============================================================= -->


  <xsl:template name="append-pub-type">
    <!-- adds a value mapped for @pub-type, enclosed in parenthesis,
         to a string -->
    <xsl:for-each select="@pub-type">
      <xsl:text> (</xsl:text>
      <span class="data">
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
      </span>
      <xsl:text>)</xsl:text>
    </xsl:for-each>
  </xsl:template>


  <xsl:template name="metadata-labeled-entry">
    <xsl:param name="label"/>
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <xsl:call-template name="metadata-entry">
      <xsl:with-param name="contents">
        <xsl:if test="normalize-space($label)">
          <span class="generated">
            <xsl:copy-of select="$label"/>
            <xsl:text>: </xsl:text>
          </span>
        </xsl:if>
        <xsl:choose>
          <xsl:when test="$label = 'DOI'">
            <a href="http://dx.doi.org/{$contents}">
              http://dx.doi.org/<xsl:value-of select="$contents"/>
            </a>
          </xsl:when>
          <xsl:otherwise>
            <xsl:copy-of select="$contents"/>
          </xsl:otherwise>
        </xsl:choose>
        
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>


  <xsl:template name="metadata-entry">
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <p class="metadata-entry">
      <xsl:copy-of select="$contents"/>
    </p>
  </xsl:template>


  <xsl:template name="metadata-area">
    <xsl:param name="label"/>
    <xsl:param name="contents">
      <xsl:apply-templates/>
    </xsl:param>
    <div class="metadata-area">
      <xsl:if test="normalize-space($label)">
        <xsl:call-template name="metadata-labeled-entry">
          <xsl:with-param name="label">
            <xsl:copy-of select="$label"/>
          </xsl:with-param>
          <xsl:with-param name="contents"/>
        </xsl:call-template>
      </xsl:if>
      <div class="metadata-chunk">
        <xsl:copy-of select="$contents"/>
      </div>
    </div>
  </xsl:template>


  <xsl:template name="make-label-text">
    <xsl:param name="auto" select="false()"/>
    <xsl:param name="warning" select="false()"/>
    <xsl:param name="auto-text"/>
    <xsl:choose>
      <xsl:when test="$auto">
        <span class="generated">
          <xsl:copy-of select="$auto-text"/>
        </span>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="label-text"
          select="label | @symbol"/>
        <xsl:if test="$warning and not(label|@symbol)">
          <span class="warning">
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
          </span>
        </xsl:if>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template name="assign-id">
    <xsl:variable name="id">
      <xsl:apply-templates select="." mode="id"/>
    </xsl:variable>
    <xsl:attribute name="id">
      <xsl:value-of select="$id"/>
    </xsl:attribute>
  </xsl:template>


  <xsl:template name="assign-src">
    <xsl:for-each select="@xlink:href">
      <xsl:attribute name="src">
        <xsl:value-of select="."/>
      </xsl:attribute>
    </xsl:for-each>
  </xsl:template>


  <xsl:template name="assign-href">
    <xsl:for-each select="@xlink:href">
      <xsl:attribute name="href">
        <xsl:value-of select="."/>
      </xsl:attribute>
    </xsl:for-each>
  </xsl:template>


  <xsl:template name="named-anchor">
    <!-- generates an HTML named anchor, using
         the source ID when found, otherwise a unique ID -->
    <xsl:variable name="id">
      <xsl:value-of select="@id"/>
      <xsl:if test="not(normalize-space(@id))">
        <xsl:value-of select="generate-id(.)"/>
      </xsl:if>
    </xsl:variable>
    <a name="{$id}">
      <xsl:comment> named anchor </xsl:comment>
    </a>
  </xsl:template>


<!-- ============================================================= -->
<!--  Process warnings                                             -->
<!-- ============================================================= -->
<!-- Generates a list of warnings to be reported due to processing
     anomalies. -->

  <xsl:template name="process-warnings">
    <!-- returns an RTF containing all the warnings -->
    <xsl:variable name="xref-warnings">
      <xsl:for-each select="//xref[not(normalize-space())]">
        <xsl:variable name="target-label">
          <xsl:apply-templates select="key('element-by-id',@rid)"
            mode="label-text">
            <xsl:with-param name="warning" select="false()"/>
          </xsl:apply-templates>
        </xsl:variable>
      	
        <xsl:if test="not(normalize-space($target-label)) and @ref-type!='aff'
        	or not(normalize-space($target-label)) and @ref-type='aff' 
        	and count(/article/front/article-meta//aff) > 1">
          <!-- if we failed to get a label with no warning, and
               this is the first cross-reference to this target
               we ask again to get the warning -->
          <li>
            <xsl:apply-templates select="key('element-by-id',@rid)"
              mode="label-text">
              <xsl:with-param name="warning" select="true()"/>
            </xsl:apply-templates>
          </li>
        </xsl:if>
      </xsl:for-each>
    </xsl:variable>

    <xsl:if test="normalize-space($xref-warnings)">
      <h4>Elements are cross-referenced without labels.</h4>
      <p>Either the element should be provided a label, or their cross-reference(s) should
        have literal text content.</p>
      <ul>
        <xsl:copy-of select="$xref-warnings"/>
      </ul>
    </xsl:if>
  </xsl:template>
  
        
   

<!-- ============================================================= -->
<!--  id mode                                                      -->
<!-- ============================================================= -->
<!-- An id can be derived for any element. If an @id is given,
     it is presumed unique and copied. If not, one is generated.   -->

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
<!--  "format-date"                                                -->
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
<!--  "author-string" writes authors' names in sequence            -->
<!-- ============================================================= -->

  <xsl:template name="author-string">
    <xsl:variable name="all-contribs"
      select="/article/front/article-meta/contrib-group/contrib/name/surname |
              /article/front/article-meta/contrib-group/contrib/collab"/>
   <xsl:for-each select="$all-contribs">
      <xsl:if test="count($all-contribs) &gt; 1">
        <xsl:if test="position() &gt; 1">
          <xsl:if test="count($all-contribs) &gt; 2">,</xsl:if>
          <xsl:text> </xsl:text>
        </xsl:if>
        <xsl:if test="position() = count($all-contribs)">and </xsl:if>
      </xsl:if>
      <xsl:value-of select="."/>
    </xsl:for-each>
  </xsl:template>
  


<!-- ============================================================= -->
<!--  End stylesheet                                               -->
<!-- ============================================================= -->

</xsl:stylesheet>
