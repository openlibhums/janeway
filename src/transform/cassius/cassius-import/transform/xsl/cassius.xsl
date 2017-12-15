<?xml version="1.0"?>

<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:mml="http://www.w3.org/1998/Math/MathML"
  xmlns:xslt="http://xml.apache.org/xslt"
  xmlns="http://www.w3.org/1999/xhtml"
  exclude-result-prefixes="xlink mml">

<xsl:output method="xhtml" indent="yes" omit-xml-declaration="no" encoding="UTF-8"
    doctype-public="-//W3C//DTD XHTML 1.0 Transitional//EN"
    doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"/>

<xsl:template match="/">
<html>
<head>
  <meta charset="utf-8"></meta>
  <meta http-equiv="X-UA-Compatible" content="IE=edge"></meta>
  <title><xsl:apply-templates select="//article-title"/></title>
  <meta name="viewport" content="width=device-width, initial-scale=1"></meta>
  <link rel="stylesheet" href="cassius/cassius.css"></link>
  <link rel="stylesheet" href="cassius/cassius-content.css"></link>
  <script src="http://use.typekit.net/ria4wnw.js"></script>
  <script type="text/javascript">try{Typekit.load();}catch(e){}</script>
  <script type="text/javascript" src="cassius/jquery.js"></script>
  <script type="text/javascript" src="cassius/cassius.js"></script>
  <script src="cassius/regions/css-regions-polyfill.js"></script>
</head>

  <body>
    <div id="cassius-content">
      <h1 class="articletitle"></h1>
      <div class="authors"></div>
      <div class="affiliations"></div>
      <div class="emails"></div>


      <div class="abstract">
          <h2>Abstract</h2>
          <xsl:apply-templates select="/article/front/article-meta/abstract/p" />
          <p class="oa-info"><xsl:apply-templates select="/article/front/article-meta/permissions/copyright-statement"/>. <xsl:apply-templates select="/article/front/article-meta/permissions/license/license-p"/></p>
      </div>

      <div class="main">
          <xsl:apply-templates select="/article/body/*" />

          <div class="notes">
              <h1>Notes</h1>
              <xsl:apply-templates select="/article/back/fn-group/fn" />
          </div>

          <div class="references">
              <h1 class="ref-title">References</h1>
              <div class="section ref-list">
                  <ul>
                      <xsl:apply-templates select="/article/back//mixed-citation"/>
                  </ul>
              </div>
          </div>
      </div>
    </div>

    <article id="article"></article>

    <script type="text/cassius" id="cassius-metadata">
        <div id="cassius-metadata-block">
            <div id="cassius-title"><xsl:apply-templates select="/article/front/article-meta/title-group/article-title"/></div>
            <div id="cassius-publication"><xsl:apply-templates select="/article/front/journal-meta/journal-title-group/journal-title"/></div>
            <div id="cassius-authors"><xsl:apply-templates select="/article/front/article-meta/contrib-group"/></div>
            <div id="cassius-emails"><xsl:apply-templates select="/article/front/article-meta/contrib-group/contrib/email"/></div>
            <div id="cassius-affiliations"><xsl:call-template name="write-affilitations"/></div>
            <div id="cassius-doi"><xsl:apply-templates select="/article/front/article-meta/article-id[@pub-id-type='doi']"/></div>
            <div id="cassius-date"><xsl:apply-templates select="/article/front/article-meta/pub-date"/></div>
            <div id="cassius-volume"><xsl:apply-templates select="/article/front/article-meta/volume"/></div>
            <div id="cassius-issue"><xsl:apply-templates select="/article/front/article-meta/issue"/></div>
        </div>
    </script>
  </body>
</html>
</xsl:template>

<!-- Abstract -->

<xsl:template match="/article/front/article-meta/abstract/p">
  <xsl:element name="p">
    <xsl:apply-templates />
  </xsl:element>
</xsl:template>

<!-- Main body -->

<xsl:template match="sec">
  <xsl:element name="div">
    <xsl:attribute name="class">section</xsl:attribute>
    <xsl:apply-templates/>
  </xsl:element>
</xsl:template>

<xsl:template match="title">
  <xsl:element name="h1">
    <xsl:apply-templates/>
  </xsl:element>
</xsl:template>

<xsl:template match="/article/body/p">
  <xsl:element name="p">
    <xsl:if test="./@content-type">
      <xsl:attribute name="class">
        <xsl:value-of select="./@content-type"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:apply-templates/>
  </xsl:element>
</xsl:template>

<xsl:template match="sec/p">
  <xsl:element name="p">
    <xsl:if test="./@content-type">
      <xsl:attribute name="class">
        <xsl:value-of select="./@content-type"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:apply-templates/>
  </xsl:element>
</xsl:template>


<xsl:template match="disp-quote">
  <xsl:element name="div">
    <xsl:attribute name="class">blockquote</xsl:attribute>
    <xsl:apply-templates/>
  </xsl:element>
</xsl:template>

<xsl:template match="disp-quote/p">
  <xsl:element name="p">
    <xsl:apply-templates/>
  </xsl:element>
</xsl:template>

<!-- Tables -->

<xsl:template match="table-wrap">
  <xsl:element name="table">
    <xsl:element name="caption"><xsl:value-of select='./label'/><xsl:text>: </xsl:text><xsl:value-of select='./caption/p'/></xsl:element>
      <xsl:apply-templates/>
  </xsl:element>
</xsl:template>

<xsl:template match="table-wrap/label">
</xsl:template>

<xsl:template match="table">
  <xsl:apply-templates/>
</xsl:template>

<xsl:template match="tr">
  <xsl:element name="tr"><xsl:apply-templates/></xsl:element>
</xsl:template>

<xsl:template match="th">
  <xsl:element name="th"><xsl:apply-templates/></xsl:element>
</xsl:template>

<xsl:template match="td">
  <xsl:element name="td"><xsl:apply-templates/></xsl:element>
</xsl:template>

<!-- back matter -->
<xsl:template match="/article/back/fn-group/fn">
  <xsl:element name="div">
    <xsl:attribute name="class">footnote</xsl:attribute>
    <xsl:element name="p">
      <xsl:element name="span">
        <xsl:attribute name="class">generated</xsl:attribute>
        <xsl:element name="a">
          <xsl:attribute name="href">
            <xsl:text>#xr</xsl:text>
            <xsl:number level="any" count="fn" from="back"/>
            <xsl:text>--fragment</xsl:text>
          </xsl:attribute>
          <xsl:attribute name="id">
            <xsl:text>fn</xsl:text>
            <xsl:number level="any" count="fn" from="back"/>
          </xsl:attribute>
          <xsl:number level="any" count="fn" from="back"/>
        </xsl:element>
      </xsl:element>
      <xsl:text> </xsl:text>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:element>
</xsl:template>

<xsl:template match="/article/back//mixed-citation">
  <xsl:element name="a">
          <xsl:attribute name="id">
            <xsl:value-of select="../@id"/>
          </xsl:attribute>
        </xsl:element>
  <xsl:element name="li">
    <xsl:attribute name="class">ref-content</xsl:attribute>
    <xsl:apply-templates />
  </xsl:element>
</xsl:template>

<!-- in-text footnotes -->

<xsl:template match="xref[@ref-type='fn']">
  <xsl:element name="a">
    <xsl:attribute name="class">footnote</xsl:attribute>
    <xsl:attribute name="href">
      <xsl:text>#fn</xsl:text>
      <xsl:number level="any" count="xref[@ref-type='fn']"/>
      <xsl:text>--fragment</xsl:text>
    </xsl:attribute>
    <xsl:attribute name="id">
      <xsl:text>xr</xsl:text>
      <xsl:number level="any" count="xref[@ref-type='fn']"/>
    </xsl:attribute>
    <xsl:element name="sup">
      <xsl:number level="any" count="xref[@ref-type='fn']"/>
    </xsl:element>
  </xsl:element>
</xsl:template>


<!-- in-text bibliography refenences -->

<xsl:template match="xref[@ref-type='bibr']">
  <xsl:element name="a">
    <xsl:attribute name="class">bibliography_link</xsl:attribute>
    <xsl:attribute name="href">
      <xsl:text>#</xsl:text>
      <xsl:value-of select="@rid"/>
      <xsl:text>--fragment</xsl:text>
    </xsl:attribute>

    <xsl:apply-templates/>

  </xsl:element>
</xsl:template>

<!-- Author names -->
  <xsl:template name="author-string">
    <xsl:variable name="all-contribs"
      select="/article/front/article-meta/contrib-group/contrib[@contrib-type='author']/name |
              /article/front/article-meta/contrib-group/contrib/collab"/>
   <xsl:for-each select="$all-contribs">
      <xsl:if test="count($all-contribs) &gt; 1">
        <xsl:if test="position() &gt; 1">
          <xsl:if test="count($all-contribs) &gt; 2">,</xsl:if>
          <xsl:text> </xsl:text>
        </xsl:if>
        <xsl:if test="position() = count($all-contribs)">and </xsl:if>
      </xsl:if>
      <xsl:call-template name="write-name"/><xsl:element name="sup"><xsl:number count="contrib[@contrib-type='author']"/></xsl:element>
    </xsl:for-each>
  </xsl:template>

  <xsl:template match="/article/front/article-meta/contrib-group">
        <!-- (surname, given-names?, prefix?, suffix?) -->
        <xsl:call-template name="author-string"/>
  </xsl:template>

  <xsl:template name="write-name">
    <xsl:apply-templates select="prefix" mode="inline-name"/>
    <xsl:apply-templates select="surname[../@name-style='eastern']"
      mode="inline-name"/>
    <xsl:apply-templates select="given-names" mode="inline-name"/>
    <xsl:apply-templates select="surname[not(../@name-style='eastern')]"
      mode="inline-name"/>
    <xsl:apply-templates select="suffix" mode="inline-name"/>
  </xsl:template>

  <xsl:template name="write-affilitations">
  <xsl:variable name="all-contribs" select="/article/front/article-meta/aff"></xsl:variable>
    <xsl:for-each select="$all-contribs">
      <xsl:if test="count($all-contribs) &gt; 1">
        <xsl:if test="position() &gt; 1">
          <xsl:if test="count($all-contribs) &gt; 2">,</xsl:if>
          <xsl:text> </xsl:text>
        </xsl:if>
        <xsl:if test="position() = count($all-contribs)">and </xsl:if>
      </xsl:if>
      <xsl:number/><xsl:text>.) </xsl:text><xsl:value-of select="."/>
    </xsl:for-each>
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

<xsl:template match="/article/front/article-meta/contrib-group/contrib/email">
<xsl:element name="a">
<xsl:attribute name="href"><xsl:text>mailto:</xsl:text><xsl:value-of select="."/></xsl:attribute>
<xsl:value-of select="."/>
</xsl:element>
</xsl:template>



  <!-- images -->

<xsl:template match="fig">
  <xsl:element name="figure">
    <xsl:apply-templates/>
    <xsl:element name="figcaption">
      <xsl:value-of select='./label'/><xsl:text>: </xsl:text><xsl:value-of select='./caption/p'/>
    </xsl:element>
  </xsl:element>
</xsl:template>

<xsl:template match="graphic">
  <xsl:element name="img">
    <xsl:attribute name="src"><xsl:value-of select="@xlink:href"/></xsl:attribute>
    <xsl:apply-templates/>
  </xsl:element>
</xsl:template>

<xsl:template match="caption">
</xsl:template>

<xsl:template match="fig/label">
</xsl:template>

  <!-- string-name elements are written as is -->

  <xsl:template match="string-name">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="string-name/*">
    <xsl:apply-templates/>
  </xsl:template>

<!-- Date formatting -->
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

  <xsl:template match="pub-date">
    <xsl:call-template name="format-date"/>
  </xsl:template>

<!-- Text formatting -->

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

  <xsl:template match="uri">
    <xsl:element name="a">
      <xsl:attribute name="href">
        <xsl:value-of select="."/>
      </xsl:attribute>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>
