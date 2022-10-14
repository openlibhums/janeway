<xsl:stylesheet version="1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:mml="http://www.w3.org/1998/Math/MathML" xmlns:xs="http://www.w3.org/2001/XMLSchema"
                xmlns:tei="http://www.tei-c.org/ns/1.0"
                exclude-result-prefixes="xsi xs xlink mml">

    <xsl:output method="html" indent="yes" encoding="utf-8"/>

    <xsl:variable name="upperspecchars" select="'ÁÀÂÄÉÈÊËÍÌÎÏÓÒÔÖÚÙÛÜ'"/>
    <xsl:variable name="uppernormalchars" select="'AAAAEEEEIIIIOOOOUUUU'"/>
    <xsl:variable name="smallspecchars" select="'áàâäéèêëíìîïóòôöúùûü'"/>
    <xsl:variable name="smallnormalchars" select="'aaaaeeeeiiiioooouuuu'"/>
    <xsl:variable name="uppercase" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
    <xsl:variable name="smallcase" select="'abcdefghijklmnopqrstuvwxyz'"/>
    <xsl:variable name="allcase" select="concat($smallcase, $uppercase)"/>

    <xsl:template match="/">
        <xsl:call-template name="metatags"/>
        <xsl:apply-templates select="//body/@* | //body/node()"/>
        <xsl:apply-templates select="//back/*"/>

        <!-- and handle TEI -->
        <xsl:apply-templates select="/tei:TEI/tei:text/tei:body"/>
    </xsl:template>

    <xsl:template match="//body/@*">
        <xsl:copy>
            <xsl:apply-templates select="//body/@*"/>
        </xsl:copy>
    </xsl:template>


    <xsl:template name="supplementary-material">
        <div id="supplementary-material">
            <xsl:if test="//supplementary-material[not(object-id)]">
                <ul class="supplementary-material">
                <xsl:for-each select="//supplementary-material[not(object-id)]/ext-link">
                    <li>
                        <a>
                            <xsl:attribute name="href"><xsl:value-of select="concat('[', @xlink:href, ']')"/></xsl:attribute>
                            <xsl:attribute name="download"/>
                            <xsl:apply-templates/>
                        </a>
                        <xsl:for-each select="../p">
                            <xsl:apply-templates select="."/>
                        </xsl:for-each>
                    </li>
                </xsl:for-each>
                </ul>
            </xsl:if>
        </div>
    </xsl:template>


    <xsl:template name="metatags">
        <div id="metatags">
            <xsl:if test="//article-meta/permissions">
                <meta name="DC.Rights">
                    <xsl:attribute name="content">
                        <xsl:value-of select="//article-meta/permissions/copyright-statement"/><xsl:text>. </xsl:text><xsl:value-of select="translate(//article-meta/permissions/license, '&#10;&#9;', '')"/>
                    </xsl:attribute>
                </meta>
            </xsl:if>
            <xsl:for-each select="//article-meta/contrib-group/contrib">
                <meta name="DC.Contributor">
                    <xsl:attribute name="content">
                        <xsl:choose>
                            <xsl:when test="name">
                                <xsl:value-of select="concat(name/given-names, ' ', name/surname)"/>
                                <xsl:if test="name/suffix">
                                    <xsl:value-of select="concat(' ', name/suffix)"/>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="collab">
                                <xsl:value-of select="collab"/>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:attribute>
                </meta>
            </xsl:for-each>
            <xsl:for-each select="//funding-group/award-group">
                <meta name="citation_funding_source">
                    <xsl:attribute name="content">
                        <xsl:value-of select="concat('citation_funder=', .//institution, ';citation_grant_number=', award-id, ';citation_grant_recipient=')"/>
                        <xsl:value-of select="concat(principal-award-recipient/name/given-names, ' ', principal-award-recipient/name/surname)"/>
                        <xsl:for-each select="principal-award-recipient/name/suffix">
                            <xsl:value-of select="concat(' ', .)"/>
                        </xsl:for-each>
                    </xsl:attribute>
                </meta>
            </xsl:for-each>
            <xsl:for-each select="//article-meta/contrib-group/contrib[@contrib-type='author']">
                <xsl:variable name="type" select="@contrib-type"/>
                <meta name="citation_{$type}">
                    <xsl:attribute name="content">
                        <xsl:choose>
                            <xsl:when test="name">
                                <xsl:value-of select="concat(name/given-names, ' ', name/surname)"/>
                                <xsl:if test="name/suffix">
                                    <xsl:value-of select="concat(' ', name/suffix)"/>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="collab">
                                <xsl:value-of select="collab"/>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:attribute>
                </meta>
                <xsl:for-each select="aff[not(@id)] | xref[@ref-type='aff'][@rid]">
                    <xsl:choose>
                        <xsl:when test="name() = 'aff'">
                            <xsl:for-each select="institution | email">
                                <meta name="citation_{$type}_{name()}">
                                    <xsl:attribute name="content">
                                        <xsl:value-of select="."/>
                                    </xsl:attribute>
                                </meta>
                            </xsl:for-each>
                        </xsl:when>
                        <xsl:when test="name() = 'xref'">
                            <xsl:variable name="rid" select="@rid"/>
                            <xsl:for-each select="//aff[@id=$rid]/institution | //aff[@id=$rid]/email">
                                <meta name="citation_{$type}_{name()}">
                                    <xsl:attribute name="content">
                                        <xsl:value-of select="."/>
                                    </xsl:attribute>
                                </meta>
                            </xsl:for-each>
                        </xsl:when>
                    </xsl:choose>
                </xsl:for-each>
                <xsl:if test="xref[@ref-type='corresp'][@rid]">
                    <xsl:variable name="rid" select="xref[@ref-type='corresp']/@rid"/>
                    <xsl:if test="//corresp[@id=$rid]/email">
                        <meta name="citation_{$type}_email">
                            <xsl:attribute name="content">
                                <xsl:value-of select="//corresp[@id=$rid]/email"/>
                            </xsl:attribute>
                        </meta>
                    </xsl:if>
                </xsl:if>
                <xsl:if test="contrib-id[@contrib-id-type='orcid']">
                    <meta name="citation_{$type}_orcid">
                        <xsl:attribute name="content">
                            <xsl:value-of select="contrib-id[@contrib-id-type='orcid']"/>
                        </xsl:attribute>
                    </meta>
                </xsl:if>
            </xsl:for-each>
            <xsl:for-each select="//ref-list/ref">
                <xsl:variable name="citation_journal" select="element-citation[@publication-type='journal']/source"/>
                <xsl:variable name="citation_string">
                    <xsl:if test="$citation_journal">
                        <xsl:value-of select="concat(';citation_journal_title=', $citation_journal)"/>
                    </xsl:if>
                    <xsl:for-each select=".//person-group[@person-group-type='author']/name | .//person-group[@person-group-type='author']/collab">
                        <xsl:choose>
                            <xsl:when test="name() = 'name'">
                                <xsl:value-of select="concat(';citation_author=', given-names, '. ', surname)"/>
                                <xsl:if test="suffix">
                                    <xsl:value-of select="concat(' ', suffix)"/>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="name() = 'collab'">
                                <xsl:value-of select="concat(';citation_author=', .)"/>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                    <xsl:for-each select=".//article-title | element-citation[not(@publication-type='journal')]/source">
                        <xsl:value-of select="concat(';citation_title=', .)"/>
                    </xsl:for-each>
                    <xsl:if test=".//fpage">
                        <xsl:value-of select="concat(';citation_pages=', .//fpage)"/>
                        <xsl:if test=".//lpage">
                            <xsl:value-of select="concat('-', .//lpage)"/>
                        </xsl:if>
                    </xsl:if>
                    <xsl:if test=".//volume">
                        <xsl:value-of select="concat(';citation_volume=', .//volume)"/>
                    </xsl:if>
                    <xsl:if test=".//year">
                        <xsl:value-of select="concat(';citation_year=', .//year)"/>
                    </xsl:if>
                    <xsl:if test=".//pub-id[@pub-id-type='doi']">
                        <xsl:value-of select="concat(';citation_doi=', .//pub-id[@pub-id-type='doi'])"/>
                    </xsl:if>
                </xsl:variable>
                <xsl:if test="string-length($citation_string)>1">
                    <meta name="citation_reference">
                        <xsl:attribute name="content">
                            <xsl:value-of select="substring-after($citation_string, ';')"/>
                        </xsl:attribute>
                    </meta>
                </xsl:if>
            </xsl:for-each>
        </div>
    </xsl:template>

    <xsl:template match="article-meta/title-group/article-title">
        <div id="article-title">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="custom-meta-group">
        <xsl:if test="custom-meta[@specific-use='meta-only']/meta-name[text()='Author impact statement']/following-sibling::meta-value">
            <div id="impact-statement">
                <xsl:apply-templates select="custom-meta[@specific-use='meta-only']/meta-name[text()='Author impact statement']/following-sibling::meta-value/node()"/>
            </div>
        </xsl:if>
    </xsl:template>

    <!-- Author list -->
    <xsl:template match="contrib-group[not(@content-type)]">
        <xsl:apply-templates/>
        <xsl:if test="contrib[@contrib-type='author'][not(@id)]">
            <div id="author-info-group-authors">
                <xsl:apply-templates select="contrib[@contrib-type='author'][not(@id)]"/>
            </div>
        </xsl:if>
    </xsl:template>

    <xsl:template match="contrib[@contrib-type='author'][not(@id)]">
        <xsl:apply-templates select="collab"/>
    </xsl:template>

    <xsl:template match="contrib//collab">
        <h4 class="equal-contrib-label">
            <xsl:apply-templates/>
        </h4>
        <xsl:variable name="contrib-id">
            <xsl:apply-templates select="../contrib-id"/>
        </xsl:variable>
        <xsl:if test="../../..//contrib[@contrib-type='author non-byline']/contrib-id[text()=$contrib-id]">
            <ul>
                <xsl:for-each
                        select="../../..//contrib[@contrib-type='author non-byline']/contrib-id[text()=$contrib-id]">
                    <li>
                        <xsl:if test="position()=1">
                            <xsl:attribute name="class">
                                <xsl:value-of select="'first'"/>
                            </xsl:attribute>
                        </xsl:if>
                        <xsl:if test="position()=last()">
                            <xsl:attribute name="class">
                                <xsl:value-of select="'last'"/>
                            </xsl:attribute>
                        </xsl:if>
                        <xsl:value-of select="../name/given-names"/>
                        <xsl:text> </xsl:text>
                        <xsl:value-of select="../name/surname"/>
                        <xsl:text>, </xsl:text>
                        <xsl:for-each select="../aff">
                            <xsl:call-template name="collabaff"/>
                            <xsl:if test="position() != last()">
                                <xsl:text>; </xsl:text>
                            </xsl:if>
                        </xsl:for-each>
                    </li>
                </xsl:for-each>
            </ul>
        </xsl:if>
    </xsl:template>

    <xsl:template name="collabaff">
        <span class="aff">
            <xsl:for-each select="@* | node()">
                <xsl:choose>
                    <xsl:when test="name() = 'institution'">
                        <span class="institution">
                            <xsl:value-of select="."/>
                        </span>
                    </xsl:when>
                    <xsl:when test="name()='country'">
                        <span class="country">
                            <xsl:value-of select="."/>
                        </span>
                    </xsl:when>
                    <xsl:when test="name()='addr-line'">
                        <span class="addr-line">
                            <xsl:apply-templates mode="authorgroup"/>
                        </span>
                    </xsl:when>
                    <xsl:when test="name()=''">
                        <xsl:value-of select="."/>
                    </xsl:when>
                    <xsl:otherwise>
                        <span class="{name()}">
                            <xsl:value-of select="."/>
                        </span>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>

        </span>
    </xsl:template>

    <xsl:template match="addr-line/named-content" mode="authorgroup">
        <span class="named-content">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <!-- ==== FRONT MATTER START ==== -->

    <xsl:template match="surname | given-names | name">
        <span class="nlm-given-names">
            <xsl:value-of select="given-names"/>
        </span>
        <xsl:text> </xsl:text>
        <span class="nlm-surname">
            <xsl:value-of select="surname"/>
        </span>
        <xsl:text>, </xsl:text>
        <xsl:value-of select="name"/>
    </xsl:template>

    <!-- ==== Data set start ==== -->
    <xsl:template match="sec[@sec-type='datasets']">
        <div id="datasets">
            <xsl:apply-templates/>
        </div>
    </xsl:template>
    <xsl:template match="sec[@sec-type='datasets']/title"/>
    <xsl:template match="related-object">
        <span class="{name()}">
            <xsl:if test="@id">
                <xsl:attribute name="id">
                    <xsl:value-of select="@id"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </span>
    </xsl:template>
    <xsl:template match="related-object/collab">
        <span class="{name()}">
            <xsl:apply-templates/>
        </span>
    </xsl:template>
    <xsl:template match="related-object/name">
        <span class="name">
            <xsl:value-of select="surname"/>
            <xsl:text> </xsl:text>
            <xsl:value-of select="given-names"/>
            <xsl:if test="suffix">
                <xsl:text> </xsl:text>
                <xsl:value-of select="suffix"/>
            </xsl:if>
        </span>
    </xsl:template>
    <xsl:template match="related-object/year">
        <span class="{name()}">
            <xsl:apply-templates/>
        </span>
    </xsl:template>
    <xsl:template match="related-object/source">
        <span class="{name()}">
            <xsl:apply-templates/>
        </span>
    </xsl:template>
    <xsl:template match="related-object/x">
        <span class="{name()}">
            <xsl:apply-templates/>
        </span>
    </xsl:template>
    <xsl:template match="related-object/etal">
        <span class="{name()}">
            <xsl:text>et al.</xsl:text>
        </span>
    </xsl:template>
    <xsl:template match="related-object/comment">
        <span class="{name()}">
            <xsl:apply-templates/>
        </span>
    </xsl:template>
    <xsl:template match="related-object/object-id">
        <span class="{name()}">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <!-- author-notes -->
    <xsl:template match="author-notes">
        <xsl:apply-templates/>
        <xsl:if test="fn[@fn-type='present-address']">
            <div id="author-info-additional-address">
                <ul class="additional-address-items">
                    <xsl:apply-templates select="fn[@fn-type='present-address']"/>
                </ul>
            </div>
        </xsl:if>

        <xsl:if test="fn[@fn-type='con'] | fn[@fn-type='other'] | fn[@fn-type='deceased']">
            <div id="author-info-equal-contrib">
                <xsl:apply-templates select="fn[@fn-type='con']"/>
            </div>
            <div id="author-info-other-footnotes">
                <xsl:apply-templates select="fn[@fn-type='other']"/>
                <xsl:apply-templates select="fn[@fn-type='deceased']"/>
            </div>
        </xsl:if>
        <div id="author-info-contributions">
            <xsl:apply-templates select="ancestor::article/back//fn-group[@content-type='author-contribution']"/>
        </div>
    </xsl:template>

    <xsl:template match="author-notes/fn[@fn-type='con']">
        <section class="equal-contrib">
                <xsl:apply-templates/>:
            <xsl:variable name="contriputeid">
                <xsl:value-of select="@id"/>
            </xsl:variable>
            <ul class="equal-contrib-list">
                <xsl:for-each select="../../contrib-group/contrib/xref[@rid=$contriputeid]">
                    <li class="equal-contributor">
                        <xsl:value-of select="../name/given-names"/>
                        <xsl:text> </xsl:text>
                        <xsl:value-of select="../name/surname"/>
                    </li>
                </xsl:for-each>
            </ul>
        </section>
    </xsl:template>

    <xsl:template match="fn-group">
        <h2>Notes</h2>
        <ol class="footnotes">
            <xsl:apply-templates/>
        </ol>
    </xsl:template>

    <xsl:template match="fn-group/fn">
        <xsl:variable name="fn-id">
            <xsl:value-of select="@id"/>
        </xsl:variable>
          <xsl:variable name="nm-number">
              <xsl:number level="any" count="xref[@rid=@id]" from="article | sub-article | response"/>
          </xsl:variable>
          <li id="{$fn-id}">
              <xsl:apply-templates/>
            <xsl:for-each select="//xref[@rid=$fn-id]">
              <xsl:variable name="i"><xsl:value-of select="string(position())"></xsl:value-of></xsl:variable>
              [<a class="footnotemarker"  href="#{$fn-id}-nm{$i}"><sup>^</sup></a>]
            </xsl:for-each>
          </li>
    </xsl:template>

    <xsl:template match="fn-group/fn/p">
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="author-notes/fn[@fn-type='con']/p">
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="author-notes/fn[@fn-type='other'] | author-notes/fn[@fn-type='deceased']">
        <xsl:variable name="fnid">
            <xsl:value-of select="@id"/>
        </xsl:variable>
        <div class="foot-note" id="{$fnid}">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="author-notes/fn[@fn-type='other']/p | author-notes/fn[@fn-type='deceased']/p">
        <p>
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <xsl:template match="author-notes/corresp">
        <li>
            <xsl:apply-templates select="email" mode="corresp"/>
        </li>
    </xsl:template>

    <xsl:template match="email" mode="corresp">
        <a>
            <xsl:attribute name="href">
                <xsl:value-of select="concat('mailto:',.)"/>
            </xsl:attribute>
            <xsl:apply-templates/>
        </a>
        <xsl:variable name="contriputeid">
            <xsl:value-of select="../@id"/>
        </xsl:variable>
        <xsl:variable name="given-names">
            <xsl:choose>
                <xsl:when test="../../../contrib-group/contrib/xref[@rid=$contriputeid][1]/../name/given-names">
                    <xsl:value-of select="../../../contrib-group/contrib/xref[@rid=$contriputeid][1]/../name/given-names"/>
                </xsl:when>
                <xsl:when test="ancestor::contrib/name/given-names">
                    <xsl:value-of select="ancestor::contrib/name/given-names"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="surname">
            <xsl:choose>
                <xsl:when test="../../../contrib-group/contrib/xref[@rid=$contriputeid][1]/../name/surname">
                    <xsl:value-of select="../../../contrib-group/contrib/xref[@rid=$contriputeid][1]/../name/surname"/>
                </xsl:when>
                <xsl:when test="ancestor::contrib/name/surname">
                    <xsl:value-of select="ancestor::contrib/name/surname"/>
                </xsl:when>
            </xsl:choose>
        </xsl:variable>

        <xsl:if test="$given-names != '' and $surname != ''">
            <xsl:text> (</xsl:text>
            <xsl:value-of select="translate($given-names, concat($smallcase, $smallspecchars, '. '), '')"/>
            <xsl:value-of select="translate($surname, concat($smallcase, $smallspecchars, '. '), '')"/>
            <xsl:text>)</xsl:text>
        </xsl:if>
    </xsl:template>

    <xsl:template match="author-notes/fn[@fn-type='present-address']">
        <li>
            <span class="present-address-intials">
                <xsl:variable name="contriputeid">
                    <xsl:value-of select="@id"/>
                </xsl:variable>
                <xsl:for-each select="../../contrib-group/contrib/xref[@rid=$contriputeid]">
                    <xsl:text>--</xsl:text>
                    <xsl:value-of select="translate(../name/given-names, concat($smallcase, '. '), '')"/>
                    <xsl:text>-</xsl:text>
                    <xsl:value-of select="translate(../name/surname, concat($smallcase, '. '), '')"/>
                    <xsl:text>:</xsl:text>
                </xsl:for-each>
            </span>
            <xsl:text> Present address:</xsl:text>
            <br/>
            <xsl:apply-templates/>
        </li>
    </xsl:template>

    <xsl:template match="author-notes/fn[@fn-type='present-address']/p">
        <xsl:apply-templates/>
    </xsl:template>

    <!-- funding-group -->
    <xsl:template match="funding-group">
        <div id="author-info-funding">
            <ul class="funding-group">
                <xsl:apply-templates/>
            </ul>
            <xsl:if test="funding-statement">
                <p class="funding-statement">
                    <xsl:value-of select="funding-statement"/>
                </p>
            </xsl:if>
        </div>
    </xsl:template>
    <xsl:template match="funding-group/award-group">
        <li>
            <xsl:apply-templates/>
        </li>
    </xsl:template>
    <xsl:template match="funding-source">
        <h4 class="funding-source">
            <xsl:apply-templates/>
        </h4>
    </xsl:template>
    <xsl:template match="funding-source/institution-wrap">
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="institution">
        <span class="institution">
            <xsl:apply-templates/>
        </span>
    </xsl:template>
    <xsl:template match="award-id">
        <h5 class="award-id">
            <xsl:apply-templates/>
        </h5>
    </xsl:template>

    <xsl:template match="principal-award-recipient">
        <ul class="principal-award-recipient">
            <xsl:apply-templates/>
        </ul>
    </xsl:template>
    <xsl:template
            match="principal-award-recipient/surname | principal-award-recipient/given-names | principal-award-recipient/name">
        <li class="name">
            <xsl:value-of select="given-names"/>
            <xsl:text> </xsl:text>
            <xsl:value-of select="surname"/>
        </li>
        <xsl:value-of select="name"/>
    </xsl:template>

    <xsl:template match="funding-statement" name="funding-statement">
        <p class="funding-statement">
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <xsl:template match="funding-statement"/>
    <!-- fn-group -->

    <xsl:template name="article-info-history">
        <div>
            <xsl:attribute name="id"><xsl:value-of select="'article-info-history'"/></xsl:attribute>
            <ul>
                <xsl:attribute name="class"><xsl:value-of select="'publication-history'"/></xsl:attribute>
                <xsl:for-each select="//history/date[@date-type]">
                    <xsl:apply-templates select="." mode="publication-history-item"/>
                </xsl:for-each>
                <xsl:apply-templates select="//article-meta/pub-date[@date-type]" mode="publication-history-item">
                    <xsl:with-param name="date-type" select="'published'"/>
                </xsl:apply-templates>
            </ul>
        </div>
    </xsl:template>

    <xsl:template match="date | pub-date" mode="publication-history-item">
        <xsl:param name="date-type" select="string(@date-type)"/>
        <li>
            <xsl:attribute name="class"><xsl:value-of select="$date-type"/></xsl:attribute>
            <span>
                <xsl:attribute name="class"><xsl:value-of select="concat($date-type, '-label')"/></xsl:attribute>
                <xsl:call-template name="camel-case-word"><xsl:with-param name="text" select="$date-type"/></xsl:call-template>
            </span>
            <xsl:variable name="month-long">
                <xsl:call-template name="month-long">
                    <xsl:with-param name="month"/>
                </xsl:call-template>
            </xsl:variable>
            <xsl:value-of select="concat(' ', $month-long, ' ', day, ', ', year, '.')"/>
        </li>
    </xsl:template>
    <xsl:template match="fn-group[@content-type='ethics-information']">
        <div id="article-info-ethics">
            <xsl:apply-templates/>
        </div>
    </xsl:template>
    <xsl:template match="fn-group[@content-type='ethics-information']/fn">
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="fn-group[@content-type='ethics-information']/title"/>
    <xsl:template match="contrib[@contrib-type='editor']" mode="article-info-reviewing-editor">
        <div id="article-info-reviewing-editor">
            <div>
                <xsl:attribute name="class"><xsl:value-of select="'acta-article-info-reviewingeditor-text'"/></xsl:attribute>
                <xsl:apply-templates select="node()"/>
            </div>
        </div>
    </xsl:template>

    <xsl:template match="fn-group[@content-type='competing-interest']">
        <div id="author-info-competing-interest">
            <ul class="fn-conflict">
                <xsl:apply-templates/>
            </ul>
        </div>
    </xsl:template>
    <xsl:template match="fn-group[@content-type='competing-interest']/fn">
        <li>
            <xsl:apply-templates/>
        </li>
    </xsl:template>

    <!-- permissions -->
    <xsl:template match="permissions">
        <div>
            <xsl:choose>
                <xsl:when test="parent::article-meta">
                    <xsl:attribute name="id">
                        <xsl:value-of select="'article-info-license'"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="class">
                        <xsl:value-of select="'copyright-and-license'"/>
                    </xsl:attribute>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:apply-templates/>
            <xsl:if test="parent::article-meta">
                <xsl:apply-templates select="//body//permissions"/>
            </xsl:if>
        </div>
    </xsl:template>

    <xsl:template match="permissions/copyright-statement">
        <ul class="copyright-statement">
            <li>
                <xsl:apply-templates/>
            </li>
        </ul>
    </xsl:template>

    <xsl:template match="license">
        <div class="license">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="license-p">
        <p>
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <!-- Affiliations -->
    <xsl:template match="aff[@id]">
        <div id="{@id}">
            <span class="aff">
                <xsl:apply-templates/>
            </span>
        </div>
    </xsl:template>

    <xsl:template match="aff" mode="affiliation-details">
        <span class="aff">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="aff/institution">
        <span class="institution">
            <xsl:if test="@content-type">
                <xsl:attribute name="data-content-type">
                    <xsl:value-of select="@content-type"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="aff/addr-line">
        <span class="addr-line">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="addr-line/named-content">
        <span class="named-content">
            <xsl:if test="@content-type">
                <xsl:attribute name="data-content-type">
                    <xsl:value-of select="@content-type"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="aff/country">
        <span class="country">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="aff/x">
        <span class="x">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="aff//bold">
        <span class="bold">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="aff//italic">
        <span class="italic">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="aff/email">
        <xsl:variable name="email">
            <xsl:apply-templates/>
        </xsl:variable>
        <!-- if parent contains more than just email then it should have a space before email -->
        <xsl:if test="string(..) != text() and not(contains(string(..), concat(' ', text())))">
            <xsl:text> </xsl:text>
        </xsl:if>
        <a href="mailto:{$email}" class="email">
            <xsl:copy-of select="$email"/>
        </a>
    </xsl:template>

    <!-- ==== FRONT MATTER END ==== -->

    <xsl:template match="abstract">
        <xsl:variable name="data-doi" select="child::object-id[@pub-id-type='doi']/text()"/>
        <div data-doi="{$data-doi}">
            <xsl:choose>
                <xsl:when test="./title">
                    <xsl:attribute name="id">
                        <xsl:value-of select="translate(translate(./title, $uppercase, $smallcase), ' ', '-')"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:attribute name="id">
                        <xsl:value-of select="name(.)"/>
                    </xsl:attribute>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <!-- Start transforming sections to heading levels -->
    <xsl:template match="supplementary-material">
        <xsl:variable name="id">
            <xsl:value-of select="@id"/>
        </xsl:variable>
        <xsl:variable name="data-doi" select="child::object-id[@pub-id-type='doi']/text()"/>
        <div class="supplementary-material" data-doi="{$data-doi}">
            <div class="supplementary-material-expansion" id="{$id}">
                <xsl:apply-templates/>
            </div>
        </div>
    </xsl:template>

    <!-- No need to proceed sec-type="additional-information", sec-type="supplementary-material" and sec-type="datasets"-->
    <xsl:template match="sec[not(@sec-type='additional-information')][not(@sec-type='datasets')][not(@sec-type='supplementary-material')]">
        <div class="article-section">
            <xsl:if test="@sec-type">
                <xsl:attribute name="class">
                    <xsl:value-of select="concat('section ', ./@sec-type)"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates select="*[name()!='sec'] | node()"/>
        </div>
    </xsl:template>

    <xsl:template match="sec[not(@sec-type='datasets')]/title | boxed-text/caption/title">
        <xsl:if test="node() != ''">
            <xsl:element name="h{count(ancestor::sec) + 1}">
              <xsl:if test="preceding-sibling::label">
                <xsl:value-of select="preceding-sibling::label"/>&#160;</xsl:if>
                <xsl:apply-templates select="@* | node()"/>
            </xsl:element>
        </xsl:if>
    </xsl:template>

    <xsl:template match="app//sec/title">
        <xsl:element name="h{count(ancestor::sec) + 3}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <!-- END transforming sections to heading levels -->

    <xsl:template match="p">
        <xsl:if test="not(supplementary-material)">
            <xsl:choose>
                <xsl:when test="not(ancestor::list[@list-type='gloss'])">
                    <p>
                        <xsl:if test="ancestor::caption and (count(preceding-sibling::p) = 0) and (ancestor::boxed-text or ancestor::media)">
                            <xsl:attribute name="class">
                                <xsl:value-of select="'first-child'"/>
                            </xsl:attribute>
                        </xsl:if>
                        <xsl:apply-templates/>
                    </p>
                </xsl:when>
                <xsl:otherwise><xsl:apply-templates/></xsl:otherwise>
            </xsl:choose>
        </xsl:if>
        <xsl:if test="supplementary-material">
            <xsl:if test="ancestor::caption and (count(preceding-sibling::p) = 0) and (ancestor::boxed-text or ancestor::media)">
                <xsl:attribute name="class">
                    <xsl:value-of select="'first-child'"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </xsl:if>
    </xsl:template>

    <xsl:template match="ext-link">
        <xsl:if test="@ext-link-type = 'uri'">
            <a>
                <xsl:attribute name="href">
                    <xsl:choose>
                        <xsl:when test="starts-with(@xlink:href, 'www.')">
                            <xsl:value-of select="concat('http://', @xlink:href)"/>
                        </xsl:when>
                        <xsl:when test="starts-with(@xlink:href, 'doi:')">
                            <xsl:value-of select="concat('http://dx.doi.org/', substring-after(@xlink:href, 'doi:'))"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="@xlink:href"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
                <xsl:attribute name="target"><xsl:value-of select="'_blank'"/></xsl:attribute>
                <xsl:apply-templates/>
            </a>
        </xsl:if>
        <xsl:if test="@ext-link-type = 'doi'">
            <a>
                <xsl:attribute name="href">
                    <xsl:choose>
                        <xsl:when test="starts-with(@xlink:href, '10.7554/')">
                            <xsl:value-of select="concat('/lookup/doi/', @xlink:href)"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="concat('http://dx.doi.org/', @xlink:href)"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:attribute>
                <xsl:apply-templates/>
            </a>
        </xsl:if>
    </xsl:template>

    <!-- START handling citation objects -->
    <xsl:template match="xref">
      <a>
          <xsl:attribute name="class">
              <xsl:value-of select="concat('xref-', ./@ref-type)"/>
          </xsl:attribute>
          <xsl:attribute name="href">
              <!-- If xref has multiple elements in rid, then the link should points to 1st -->
              <xsl:choose>
                  <xsl:when test="contains(@rid, ' ')">
                      <xsl:value-of select="concat('#',substring-before(@rid, ' '))"/>
                  </xsl:when>
                  <xsl:otherwise>
                      <xsl:value-of select="concat('#',@rid)"/>
                  </xsl:otherwise>
              </xsl:choose>
          </xsl:attribute>
          <xsl:choose>
            <xsl:when test="contains(@ref-type, 'fn')">
              <!-- Construction of the note mention (nm) ID combining the fn item being referenced (rid) with the sequential
                  number of this mention of the fn. So if an xref of type 'fn' with the same rid is referenced twice,
                  they will get uniquely identifiable IDs. As an example, two mentions of an fn with rid 'fn1' would lead to
                  two objects with ids of 'fn1-nm1' and 'fn1-nm2'. Then the fn in the footnotes section
                  can render individual links to each nm in the body.
              -->
              <xsl:variable name="rid" select="@rid"/>
              <xsl:attribute name="id">
                  <xsl:value-of select="@rid"/>
                  <xsl:text>-</xsl:text>
                  <xsl:text>nm</xsl:text>
                  <xsl:number level="any" count="xref[@rid=$rid]"/>
              </xsl:attribute>
              <sup><xsl:apply-templates/></sup>
            </xsl:when>
            <xsl:otherwise>
              <xsl:apply-templates/>
            </xsl:otherwise>
          </xsl:choose>
      </a>
    </xsl:template>
    <!-- END handling citation objects -->

    <!-- START Array handling -->
    <xsl:template match="array">
        <table class="array-table">
            <xsl:apply-templates/>
        </table>
    </xsl:template>
    <!-- END Array handling -->

    <!-- START Table Handling -->
    <xsl:template match="table-wrap">
        <xsl:variable name="data-doi" select="child::object-id[@pub-id-type='doi']/text()"/>
        <div class="table-wrap" data-doi="{$data-doi}">
            <xsl:apply-templates select="." mode="testing"/>
        </div>
    </xsl:template>

    <xsl:template match="table-wrap/label" mode="captionLabel">
        <span class="table-label">
            <xsl:apply-templates/>
        </span>
        <xsl:text> </xsl:text>
    </xsl:template>

    <xsl:template match="caption" name="caption">
        <xsl:choose>
            <!-- if article-title exists, make it as title.
                     Otherwise, make source -->
            <xsl:when test="parent::table-wrap">
                <xsl:if test="following-sibling::graphic">
                    <xsl:variable name="caption" select="parent::table-wrap/label/text()"/>
                    <xsl:variable name="graphics" select="following-sibling::graphic/@xlink:href"/>
                    <div class="fig-inline-img-set">
                        <a href="{$graphics}" class="figure-expand-popup" title="{$caption}">
                            <img data-img="{$graphics}" src="{$graphics}" alt="{$caption}" class="responsive-img" />
                        </a>
                    </div>
                </xsl:if>
                <div class="table-caption">
                    <xsl:apply-templates select="parent::table-wrap/label" mode="captionLabel"/>
                    <xsl:apply-templates/>
                </div>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="table-wrap/table">
      <xsl:variable name="graphics" select="./@xlink:href"/>
        <table>
         <xsl:choose>
          <xsl:when test="./@content-type = 'example'">
            <xsl:attribute name="content-type">
              <xsl:value-of select="./@content-type"/>
            </xsl:attribute>
          </xsl:when>
          <xsl:otherwise>
            <xsl:attribute name="class">article-table unstriped</xsl:attribute>
          </xsl:otherwise>
         </xsl:choose>
         <xsl:apply-templates/>
        </table>
    </xsl:template>

    <!-- Handle other parts of table -->
    <xsl:template match="thead | tr">
        <xsl:copy>
            <xsl:if test="@style">
                <xsl:attribute name="style">
                    <xsl:value-of select="@style"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="tbody" name="tbody">
        <xsl:copy>
            <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="th | td">
        <xsl:copy>
            <xsl:if test="@rowspan">
                <xsl:attribute name="rowspan">
                    <xsl:value-of select="@rowspan"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="@colspan">
                <xsl:attribute name="colspan">
                    <xsl:value-of select="@colspan"/>
                </xsl:attribute>
            </xsl:if>

            <!-- The author-callout-style-b family applies both background and foreground colour. -->
            <xsl:variable name="class">
                <xsl:if test="@align">
                    <xsl:value-of select="concat(' table-', @align)"/>
                </xsl:if>
                <xsl:if test="@valign">
                    <xsl:value-of select="concat(' table-', @valign)"/>
                </xsl:if>
                <xsl:if test="@style and starts-with(@style, 'author-callout-style-b')">
                    <xsl:value-of select="concat(' ', @style)"/>
                </xsl:if>
            </xsl:variable>

            <xsl:if test="$class != ''">
                <xsl:attribute name="class">
                    <xsl:value-of select="substring-after($class, ' ')"/>
                </xsl:attribute>
            </xsl:if>

            <xsl:if test="@style and not(starts-with(@style, 'author-callout-style-b'))">
                <xsl:attribute name="style">
                    <xsl:value-of select="@style"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="ancestor::table[@content-type ='example']">
              <xsl:attribute name="style">vertical-align: top;</xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>

    <!-- Handle Table FootNote -->
    <xsl:template match="table-wrap-foot">
        <div class="table-foot">
            <ul class="table-footnotes">
                <xsl:apply-templates/>
            </ul>
        </div>
    </xsl:template>

    <xsl:template match="table-wrap-foot/fn">
        <li class="fn">
            <xsl:if test="@id">
                <xsl:attribute name="id">
                    <xsl:value-of select="@id"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </li>
    </xsl:template>

    <xsl:template match="named-content">
        <span>
            <xsl:attribute name="class">
                <xsl:value-of select="name()"/>
                <xsl:if test="@content-type">
                    <xsl:value-of select="concat(' ', @content-type)"/>
                </xsl:if>
            </xsl:attribute>
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="inline-formula">
        <span class="inline-formula">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <!-- MathML Inline -->
  <xsl:template match="alternatives/mml:math">
    <span class="inline-formula mathml">
      <math xmlns:mml="http://www.w3.org/1998/Math/MathML">
      <xsl:copy-of select="text() | *"/>
    </math>
    </span>
  </xsl:template>

  <xsl:template match="alternatives/tex-math">
  </xsl:template>

  <xsl:template match="alternatives/graphic">
  </xsl:template>

    <xsl:template match="disp-formula">
        <p class="disp-formula">
            <xsl:if test="@id">
                <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
            <xsl:if test="label">
                <span class="disp-formula-label">
                    <xsl:value-of select="label/text()"/>
                </span>
            </xsl:if>
        </p>
    </xsl:template>


      <xsl:template match="disp-formula/tex-math">
    <div class="formula tex-math hidden">
        <xsl:copy>
          <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </div>
  </xsl:template>

  <xsl:template match="inline-formula/tex-math">
    <span class="inline-formula tex-math hidden">
        <xsl:copy>
          <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </span>
  </xsl:template>

  <!-- MathML Inline -->
  <xsl:template match="inline-formula/mml:math">
    <span class="inline-formula mathml">
      <math xmlns:mml="http://www.w3.org/1998/Math/MathML">
      <xsl:copy-of select="text() | *"/>
    </math>
    </span>
  </xsl:template>

  <!-- MathML in Div -->
  <xsl:template match="disp-formula/mml:math">
    <div class="math-formulae mathml">
      <math xmlns:mml="http://www.w3.org/1998/Math/MathML">
      <xsl:copy-of select="text() | *"/>
    </math>
    </div>
  </xsl:template>

    <!-- END Table Handling -->

    <!-- Start Figure Handling -->
    <!-- fig with atrtribute specific-use are supplement figures -->

    <!-- NOTE: PATH/LINK to be replaced -->
    <xsl:template match="fig-group">
        <!-- set main figure's DOI -->
        <xsl:variable name="data-doi" select="child::fig[1]/object-id[@pub-id-type='doi']/text()"/>
        <div class="fig-group" id="{concat('fig-group-', count(preceding::fig-group)+1)}" data-doi="{$data-doi}">
            <xsl:apply-templates select="." mode="testing"/>
        </div>
    </xsl:template>


    <xsl:template match="fig | table-wrap | boxed-text | supplementary-material | media" mode="dc-description">
        <xsl:param name="doi"/>
        <xsl:variable name="data-dc-description">
            <xsl:if test="caption/title">
                <xsl:value-of select="concat(' ', caption/title)"/>
            </xsl:if>
            <xsl:for-each select="caption/p">
                <xsl:if test="not(ext-link[@ext-link-type='doi']) and not(.//object-id[@pub-id-type='doi'])">
                    <xsl:value-of select="concat(' ', .)"/>
                </xsl:if>
            </xsl:for-each>
        </xsl:variable>
        <div data-dc-description="{$doi}">
            <xsl:value-of select="substring-after($data-dc-description, ' ')"/>
        </div>
    </xsl:template>

    <!-- individual fig in fig-group -->

    <xsl:template match="fig">
        <xsl:variable name="data-doi" select="child::object-id[@pub-id-type='doi']/text()"/>
        <xsl:choose>
          <xsl:when test="./media">
            <xsl:apply-templates/>
           </xsl:when>
           <xsl:otherwise>
          <div class="fig" data-doi="{$data-doi}">
            <xsl:apply-templates select="." mode="testing"/>
          </div>
           </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- fig caption -->
    <xsl:template match="fig//caption">
        <xsl:variable name="graphic-type">
            <xsl:choose>
                <xsl:when test="substring-after(../graphic/@xlink:href, '.') = 'gif'">
                    <xsl:value-of select="'animation'"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'graphic'"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:choose>
            <xsl:when test="not(parent::supplementary-material)">
                <div class="fig-caption">
                    <xsl:variable name="graphics" select="../graphic/@xlink:href"/>

                    <span class="fig-label">
                        <xsl:value-of select="../label/text()"/>
                    </span>
                    <xsl:text> </xsl:text>
                    <xsl:apply-templates/>
                </div>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="../label" mode="supplementary-material"/>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="supplementary-material/label">
        <xsl:apply-templates select="." mode="supplementary-material"/>
    </xsl:template>

    <xsl:template match="label" mode="supplementary-material">
        <span class="supplementary-material-label">
            <xsl:value-of select="."/>
        </span>
    </xsl:template>

    <xsl:template match="fig//caption/title | supplementary-material/caption/title">
        <span class="caption-title">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <!-- END Figure Handling -->

    <!-- body content -->
    <xsl:template match="body">
        <div class="acta-article-decision-letter">
            <xsl:apply-templates/>
        </div>
        <div id='main-text'>
            <div class="article fulltext-view">
                <xsl:apply-templates mode="testing"/>
                <xsl:call-template name="appendices-main-text"/>
            </div>
        </div>
        <div id="main-figures">
            <xsl:for-each select=".//fig[not(@specific-use)][not(parent::fig-group)] | .//fig-group">
                <xsl:apply-templates select="."/>
            </xsl:for-each>
        </div>
    </xsl:template>

    <xsl:template
            match="sec[not(@sec-type='additional-information')][not(@sec-type='datasets')][not(@sec-type='supplementary-material')]"
            mode="testing">
        <div>
            <xsl:if test="@sec-type">
                <xsl:attribute name="class">
                    <xsl:value-of select="concat('section ', translate(./@sec-type, '|', '-'))"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="@id">
                <xsl:attribute name="id">
                    <xsl:value-of select="@id"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:if test="not(@sec-type)">
                <xsl:attribute name="class">
                    <xsl:value-of select="'subsection'"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates mode="testing"/>
        </div>
    </xsl:template>

    <xsl:template match="xref" mode="testing">
        <xsl:choose>
            <xsl:when test="ancestor::fn">
                <span class="xref-table">
                    <xsl:apply-templates/>
                </span>
            </xsl:when>
            <xsl:otherwise>
                <a>
                    <xsl:attribute name="class">
                        <xsl:value-of select="concat('xref-', ./@ref-type)"/>
                    </xsl:attribute>
                    <xsl:attribute name="href">
                        <!-- If xref has multiple elements in rid, then the link should points to 1st -->
                        <xsl:choose>
                            <xsl:when test="contains(@rid, ' ')">
                                <xsl:value-of select="concat('#',substring-before(@rid, ' '))"/>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:value-of select="concat('#',@rid)"/>
                            </xsl:otherwise>
                        </xsl:choose>

                    </xsl:attribute>
                    <xsl:apply-templates/>
                </a>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="table-wrap" mode="testing">
        <div class="table-expansion">
            <xsl:if test="@id">
                <xsl:attribute name="id">
                    <xsl:value-of select="@id"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="boxed-text" mode="testing">
        <!-- For the citation links, take the id from the boxed-text -->
        <xsl:choose>
            <xsl:when test="child::object-id[@pub-id-type='doi']/text()!=''">
                <div class="boxed-text">
                    <xsl:attribute name="id">
                        <xsl:value-of select="@id"/>
                    </xsl:attribute>
                    <xsl:apply-templates/>
                </div>
            </xsl:when>
            <xsl:otherwise>
                <div>
                    <xsl:attribute name="class">
                        <xsl:value-of select="'boxed-text'"/>
                        <xsl:if test="//article/@article-type != 'research-article' and .//inline-graphic">
                            <xsl:value-of select="' insight-image'"/>
                        </xsl:if>
                    </xsl:attribute>
                    <xsl:apply-templates/>
                </div>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="//graphic[not(ancestor::fig) and not(ancestor::alternatives)]">
        <xsl:variable name="caption" select="child::caption/text()"/>
        <xsl:variable name="graphics" select="./@xlink:href"/>
        <div class="fig-inline-img-set">
            <div class="acta-fig-image-caption-wrapper">
                <div class="fig-expansion">
                    <div class="fig-inline-img">
                        <a href="{$graphics}" class="figure-expand-popup" title="{$caption}">
                            <img data-img="{$graphics}" src="{$graphics}" alt="{$caption}"/>
                        </a>
                    </div>
                    <xsl:apply-templates/>
                </div>
            </div>
        </div>
    </xsl:template>


    <xsl:template match="fig" mode="testing">
        <xsl:variable name="caption" select="child::label/text()"/>
        <xsl:variable name="id">
            <xsl:value-of select="@id"/>
        </xsl:variable>
        <xsl:variable name="graphic-type">
            <xsl:choose>
                <xsl:when test="substring-after(child::graphic/@xlink:href, '.') = 'gif'">
                    <xsl:value-of select="'animation'"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'graphic'"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:variable name="graphics" select="graphic/@xlink:href"/>
        <div id="{$id}" class="fig-inline-img-set">
	  <xsl:for-each select="graphic">
            <div class="acta-fig-image-caption-wrapper">
                <div class="fig-expansion">
                    <div class="fig-inline-img">
                        <a href="{@xlink:href}" class="figure-expand-popup" title="{$caption}">
				<img data-img="{$graphics}" src="{@xlink:href}" alt="{$caption}" class="responsive-img" />
                        </a>
                    </div>
                </div>
            </div>
	    </xsl:for-each>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="fig-group" mode="testing">
        <!-- set main figure's DOI -->
        <div class="fig-inline-img-set-carousel">
            <div class="acta-fig-slider-wrapper">
                <div class="acta-fig-slider">
                    <div class="acta-fig-slider-img acta-fig-slider-primary">
                        <!-- use variables to set src and alt -->
                        <xsl:variable name="primaryid" select="concat('#', child::fig[not(@specific-use)]/@id)"/>
                        <xsl:variable name="primarycap" select="child::fig[not(@specific-use)]//label/text()"/>
                        <xsl:variable name="graphichref" select="substring-before(concat(child::fig[not(@specific-use)]/graphic/@xlink:href, '.'), '.')"/>
                        <a href="{$primaryid}">
                            <img src="{$graphichref}" alt="{$primarycap}" class="responsive-img"/>
                        </a>
                    </div>
                    <div class="figure-carousel-inner-wrapper">
                        <div class="figure-carousel">
                            <xsl:for-each select="child::fig[@specific-use]">
                                <!-- use variables to set src and alt -->
                                <xsl:variable name="secondarycap" select="child::label/text()"/>
                                <xsl:variable name="secgraphichref" select="substring-before(concat(child::graphic/@xlink:href, '.'), '.')"/>
                                <div class="acta-fig-slider-img acta-fig-slider-secondary">
                                    <a href="#{@id}">
                                        <img src="{$secgraphichref}" alt="{$secondarycap}" class="responsive-img"/>
                                    </a>
                                </div>
                            </xsl:for-each>
                        </div>
                    </div>
                </div>
            </div>
            <div class="acta-fig-image-caption-wrapper">
                <xsl:apply-templates/>
            </div>
        </div>
    </xsl:template>

    <xsl:template match="media" mode="vimeo">
      <xsl:variable name="vimeo_url" select="./@xlink:href"/>
        <div class="media video-content">
          <div class="media-inline video-inline">
            <div class="acta-inline-video">
              <div style="padding:56.25% 0 0 0;position:relative;">
                <iframe
                  src="{$vimeo_url}"
                  style="position:absolute;top:0;left:0;width:100%;height:100%;"
                  frameborder="0" allow="autoplay; fullscreen; picture-in-picture"
                allowfullscreen="yes"
                ></iframe>
                <script src="https://player.vimeo.com/api/player.js"></script>
              </div>
            </div>
          </div>
        </div>
          <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="media" mode="youtube">
      <div class="media video-content">
        <div class="media-inline video-inline">
          <div class="acta-inline-video">
            <iframe
              width="560" height="315"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              src="{@xlink:href}" frameborder="0"
              allowfullscreen="yes"
            ></iframe>
          </div>
        </div>
      </div>
          <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="media" mode="soundcloud">
      <div class="media audio-content">
        <div class="media-inline audio-inline">
          <div class="acta-inline-audio">
            <iframe
              width="100%" height="150"
              scrolling="no" frameborder="no" allow="autoplay"
              src="{@xlink:href}"
            ></iframe>
          </div>
        </div>
      </div>
          <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="media" mode="testing">
        <xsl:choose>
            <xsl:when test="@mimetype != 'video'">
                <xsl:variable name="media-download-href"><xsl:value-of select="concat(substring-before(@xlink:href, '.'), '-download.', substring-after(@xlink:href, '.'))"/></xsl:variable>
                <!-- if mimetype is application -->
                <span class="inline-linked-media-wrapper">
                    <a href="{$media-download-href}">
                        <xsl:attribute name="download"/>
                        <i class="icon-download-alt"></i>
                        Download source data<span class="inline-linked-media-filename">
                            [<xsl:value-of
                                select="translate(translate(preceding-sibling::label, $uppercase, $smallcase), ' ', '-')"/>media-<xsl:value-of
                                select="count(preceding::media[@mimetype = 'application']) + 1"/>.<xsl:value-of
                                select="substring-after(@xlink:href, '.')"/>]
                        </span>
                    </a>
                </span>
            </xsl:when>
            <xsl:otherwise>
                <!-- otherwise -->
                <div class="media video-content">
                    <!-- set attribute -->
                    <xsl:attribute name="id">
                        <!-- <xsl:value-of select="concat('media-', @id)"/>-->
                        <xsl:value-of select="@id"/>
                    </xsl:attribute>
                    <div class="media-inline video-inline">
                        <div class="acta-inline-video">
                            <xsl:text> [video-</xsl:text><xsl:value-of select="@id"/><xsl:text>-inline] </xsl:text>

                            <div class="acta-video-links">
                                <span class="acta-video-link acta-video-link-download">
                                    <a href="[video-{@id}-download]"><xsl:attribute name="download"/>Download Video</a>

                                </span>
                            </div>
                        </div>
                    </div>
                    <xsl:apply-templates/>
                </div>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <!-- Acknowledgement -->

    <xsl:template match="ack">
        <h2>Acknowledgements</h2>
        <div id="ack-1">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="ref-list">
        <!-- We inject the references heading only when there is no title block -->
        <xsl:if test="name(*[1]) != 'title'">
          <h2>References</h2>
        </xsl:if>
        <div id="reflist">
            <xsl:apply-templates/>
        </div>
    </xsl:template>
    <xsl:template match="ref-list/title">
        <xsl:if test="node() != ''">
            <xsl:element name="h2">
                <xsl:apply-templates/>
            </xsl:element>
        </xsl:if>
    </xsl:template>

    <!-- START Reference Handling -->

   <!-- ============================================================= -->
  <!--  53. REF                                                      -->
  <!-- ============================================================= -->

  <!-- If ref/label, ref is a table row;
    If count(ref/citation) > 1, each citation is a table row -->
  <xsl:template match="ref">
    <xsl:choose>
      <xsl:when test="count(element-citation)=1">
          <p id="{parent::*/@id}">
            <xsl:apply-templates select="element-citation | nlm-citation"/>
          </p>
      </xsl:when>
      <xsl:otherwise>
        <xsl:for-each select="element-citation | nlm-citation | mixed-citation">
            <p id="{parent::*/@id}">
                <xsl:if test="parent::ref/label">
                  <xsl:apply-templates select="parent::ref/label"/>
                </xsl:if>
                <xsl:apply-templates select="."/>
            </p>
        </xsl:for-each>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- becomes content of table cell, column 1-->
  <xsl:template match="ref/label | element-citation/label">
    <strong>
      <em>
        <xsl:apply-templates/>
        <xsl:text>. </xsl:text>
      </em>
    </strong>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  54. CITATION (for NLM Archiving DTD)                         -->
  <!-- ============================================================= -->

  <!-- The citation model is mixed-context, so it is processed
     with an apply-templates (as for a paragraph)
       -except-
     if there is no PCDATA (only elements), spacing and punctuation
     also must be supplied = mode nscitation. -->

  <xsl:template match="ref/element-citation">

    <xsl:choose>
      <!-- if has no significant text content, presume that
           punctuation is not supplied in the source XML
           = transform will supply it. -->
      <xsl:when test="not(text()[normalize-space()])">
        <xsl:apply-templates mode="none"/>
      </xsl:when>

      <!-- mixed-content, processed as paragraph -->
      <xsl:otherwise>
        <xsl:apply-templates mode="nscitation"/>
      </xsl:otherwise>
    </xsl:choose>

  </xsl:template>

  <xsl:template match="mixed-citation">
      <!-- Render each mixed-citation as-is https://jats.nlm.nih.gov/archiving/tag-library/1.1/element/mixed-citation.html -->
      <!-- Only exceptions are that we want titles <source> in italics and hyperlinked uris elements-->
      <xsl:apply-templates select="source | node()" mode="nscitation"/>
      <xsl:apply-templates select="ext-link"/>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  55. NLM-CITATION (for NLM Publishing DTD)                    -->
  <!-- ============================================================= -->

  <!-- The nlm-citation model allows only element content, so
     it takes a pull template and adds punctuation. -->

  <!-- Processing of nlm-citation uses several modes, including
     citation, book, edited-book, conf, inconf, and mode "none".   -->

  <!-- Each citation-type is handled in its own template. -->


  <!-- Book or thesis -->
  <xsl:template
    match="ref/nlm-citation[@citation-type='book']
                   | ref/nlm-citation[@citation-type='thesis']">

    <xsl:variable name="augroupcount" select="count(person-group) + count(collab)"/>

    <xsl:choose>

      <xsl:when
        test="$augroupcount>1 and
                    person-group[@person-group-type!='author'] and
                    article-title ">
        <xsl:apply-templates select="person-group[@person-group-type='author']" mode="book"/>
        <xsl:apply-templates select="collab" mode="book"/>
        <xsl:apply-templates select="article-title" mode="editedbook"/>
        <xsl:text>In: </xsl:text>
        <xsl:apply-templates
          select="person-group[@person-group-type='editor']
                                 | person-group[@person-group-type='allauthors']
                                 | person-group[@person-group-type='translator']
                                 | person-group[@person-group-type='transed'] "
          mode="book"/>
        <xsl:apply-templates select="source" mode="book"/>
        <xsl:apply-templates select="edition" mode="book"/>
        <xsl:apply-templates select="volume" mode="book"/>
        <xsl:apply-templates select="trans-source" mode="book"/>
        <xsl:apply-templates select="publisher-name | publisher-loc" mode="none"/>
        <xsl:apply-templates select="year | month | time-stamp | season | access-date" mode="book"/>
        <xsl:apply-templates select="fpage | lpage" mode="book"/>
      </xsl:when>

      <xsl:when
        test="person-group[@person-group-type='author'] or
                    person-group[@person-group-type='compiler']">
        <xsl:apply-templates
          select="person-group[@person-group-type='author']
                                 | person-group[@person-group-type='compiler']"
          mode="book"/>
        <xsl:apply-templates select="collab" mode="book"/>
        <xsl:apply-templates select="source" mode="book"/>
        <xsl:apply-templates select="edition" mode="book"/>
        <xsl:apply-templates
          select="person-group[@person-group-type='editor']
                                 | person-group[@person-group-type='translator']
                                 | person-group[@person-group-type='transed'] "
          mode="book"/>
        <xsl:apply-templates select="volume" mode="book"/>
        <xsl:apply-templates select="trans-source" mode="book"/>
        <xsl:apply-templates select="publisher-name | publisher-loc" mode="none"/>
        <xsl:apply-templates select="year | month | time-stamp | season | access-date" mode="book"/>
        <xsl:apply-templates select="article-title | fpage | lpage" mode="book"/>
      </xsl:when>

      <xsl:otherwise>
        <xsl:apply-templates
          select="person-group[@person-group-type='editor']
                                 | person-group[@person-group-type='translator']
                                 | person-group[@person-group-type='transed']
                                 | person-group[@person-group-type='guest-editor']"
          mode="book"/>
        <xsl:apply-templates select="collab" mode="book"/>
        <xsl:apply-templates select="source" mode="book"/>
        <xsl:apply-templates select="edition" mode="book"/>
        <xsl:apply-templates select="volume" mode="book"/>
        <xsl:apply-templates select="trans-source" mode="book"/>
        <xsl:apply-templates select="publisher-name | publisher-loc" mode="none"/>
        <xsl:apply-templates select="year | month | time-stamp | season | access-date" mode="book"/>
        <xsl:apply-templates select="article-title | fpage | lpage" mode="book"/>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:call-template name="citation-tag-ends"/>
  </xsl:template>


  <!-- Conference proceedings -->
  <xsl:template match="ref/nlm-citation[@citation-type='confproc']">

    <xsl:variable name="augroupcount" select="count(person-group) + count(collab)"/>

    <xsl:choose>
      <xsl:when test="$augroupcount>1 and person-group[@person-group-type!='author']">
        <xsl:apply-templates select="person-group[@person-group-type='author']" mode="book"/>
        <xsl:apply-templates select="collab"/>
        <xsl:apply-templates select="article-title" mode="inconf"/>
        <xsl:text>In: </xsl:text>
        <xsl:apply-templates
          select="person-group[@person-group-type='editor']
                                 | person-group[@person-group-type='allauthors']
                                 | person-group[@person-group-type='translator']
                                 | person-group[@person-group-type='transed'] "
          mode="book"/>
        <xsl:apply-templates select="source" mode="conf"/>
        <xsl:apply-templates select="conf-name | conf-date | conf-loc" mode="conf"/>
        <xsl:apply-templates select="publisher-loc" mode="none"/>
        <xsl:apply-templates select="publisher-name" mode="none"/>
        <xsl:apply-templates select="year | month | time-stamp | season | access-date" mode="book"/>
        <xsl:apply-templates select="fpage | lpage" mode="book"/>
      </xsl:when>

      <xsl:otherwise>
        <xsl:apply-templates select="person-group" mode="book"/>
        <xsl:apply-templates select="collab" mode="book"/>
        <xsl:apply-templates select="article-title" mode="conf"/>
        <xsl:apply-templates select="source" mode="conf"/>
        <xsl:apply-templates select="conf-name | conf-date | conf-loc" mode="conf"/>
        <xsl:apply-templates select="publisher-loc" mode="none"/>
        <xsl:apply-templates select="publisher-name" mode="none"/>
        <xsl:apply-templates select="year | month | time-stamp | season | access-date" mode="book"/>
        <xsl:apply-templates select="fpage | lpage" mode="book"/>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:call-template name="citation-tag-ends"/>
  </xsl:template>


  <!-- Government and other reports, other, web, and commun -->
  <xsl:template
    match="ref/nlm-citation[@citation-type='gov']
                   | ref/nlm-citation[@citation-type='web']
                   | ref/nlm-citation[@citation-type='commun']
                   | ref/nlm-citation[@citation-type='other']">

    <xsl:apply-templates select="person-group" mode="book"/>

    <xsl:apply-templates select="collab"/>

    <xsl:choose>
      <xsl:when test="publisher-loc | publisher-name">
        <xsl:apply-templates select="source" mode="book"/>
        <xsl:choose>
          <xsl:when test="@citation-type='web'">
            <xsl:apply-templates select="edition" mode="none"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates select="edition"/>
          </xsl:otherwise>
        </xsl:choose>

        <xsl:apply-templates select="publisher-loc" mode="none"/>
        <xsl:apply-templates select="publisher-name" mode="none"/>
        <xsl:apply-templates select="year | month | time-stamp | season | access-date" mode="book"/>
        <strong><xsl:apply-templates select="article-title|gov" mode="none"/></strong>
      </xsl:when>

      <xsl:otherwise>
        <xsl:apply-templates select="article-title|gov" mode="book"/>
        <xsl:apply-templates select="source" mode="book"/>
        <xsl:apply-templates select="edition"/>
        <xsl:apply-templates select="publisher-loc" mode="none"/>
        <xsl:apply-templates select="publisher-name" mode="none"/>
        <xsl:apply-templates select="year | month | time-stamp | season | access-date" mode="book"/>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:apply-templates select="fpage | lpage" mode="book"/>

    <xsl:call-template name="citation-tag-ends"/>

  </xsl:template>


  <!-- Patents  -->
  <xsl:template match="ref/nlm-citation[@citation-type='patent']">

    <xsl:apply-templates select="person-group" mode="book"/>
    <xsl:apply-templates select="collab" mode="book"/>
    <xsl:apply-templates select="article-title | trans-title" mode="none"/>
    <xsl:apply-templates select="source" mode="none"/>
    <xsl:apply-templates select="patent" mode="none"/>
    <xsl:apply-templates select="year | month | time-stamp | season | access-date" mode="book"/>
    <xsl:apply-templates select="fpage | lpage" mode="book"/>

    <xsl:call-template name="citation-tag-ends"/>

  </xsl:template>


  <!-- Discussion  -->
  <xsl:template match="ref/nlm-citation[@citation-type='discussion']">

    <xsl:apply-templates select="person-group" mode="book"/>
    <xsl:apply-templates select="collab"/>
    <xsl:apply-templates select="article-title" mode="editedbook"/>
    <xsl:text>In: </xsl:text>
    <xsl:apply-templates select="source" mode="none"/>

    <xsl:if test="publisher-name | publisher-loc">
      <xsl:text> [</xsl:text>
      <xsl:apply-templates select="publisher-loc" mode="none"/>
      <xsl:value-of select="publisher-name"/>
      <xsl:text>]; </xsl:text>
    </xsl:if>

    <xsl:apply-templates select="year | month | time-stamp | season | access-date" mode="book"/>
    <xsl:apply-templates select="fpage | lpage" mode="book"/>

    <xsl:call-template name="citation-tag-ends"/>
  </xsl:template>


  <!-- If none of the above citation-types applies,
     use mode="none". This generates punctuation. -->
  <!-- (e.g., citation-type="journal"              -->
  <xsl:template match="nlm-citation">

    <xsl:apply-templates
      select="*[not(self::annotation) and
                                 not(self::edition) and
                                 not(self::lpage) and
                                 not(self::comment)]|text()"
      mode="none"/>

    <xsl:call-template name="citation-tag-ends"/>

  </xsl:template>


  <!-- ============================================================= -->
  <!-- person-group, mode=book                                       -->
  <!-- ============================================================= -->

  <xsl:template match="person-group" mode="book">

    <!-- XX needs fix, value is not a nodeset on the when -->
    <!--
  <xsl:choose>

    <xsl:when test="@person-group-type='editor'
                  | @person-group-type='assignee'
                  | @person-group-type='translator'
                  | @person-group-type='transed'
                  | @person-group-type='guest-editor'
                  | @person-group-type='compiler'
                  | @person-group-type='inventor'
                  | @person-group-type='allauthors'">

      <xsl:call-template name="make-persons-in-mode"/>
      <xsl:call-template name="choose-person-type-string"/>
      <xsl:call-template name="choose-person-group-end-punct"/>

    </xsl:when>

    <xsl:otherwise>
      <xsl:apply-templates mode="book"/>
    </xsl:otherwise>

  </xsl:choose>
-->

    <xsl:call-template name="make-persons-in-mode"/>
    <xsl:call-template name="choose-person-group-end-punct"/>

  </xsl:template>



  <!-- if given names aren't all-caps, use book mode -->

  <xsl:template name="make-persons-in-mode">

    <xsl:variable name="gnms" select="string(descendant::given-names)"/>

    <xsl:variable name="GNMS"
      select="translate($gnms,
      'abcdefghjiklmnopqrstuvwxyz',
      'ABCDEFGHJIKLMNOPQRSTUVWXYZ')"/>

    <xsl:choose>
      <xsl:when test="$gnms=$GNMS">
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates mode="book"/>
      </xsl:otherwise>
    </xsl:choose>

  </xsl:template>

  <xsl:template name="choose-person-group-end-punct">

    <xsl:choose>
      <!-- compiler is an exception to the usual choice pattern -->
      <xsl:when test="@person-group-type='compiler'">
        <xsl:text>. </xsl:text>
      </xsl:when>

      <!-- the usual choice pattern: semi-colon or period? -->
      <xsl:when test="following-sibling::person-group">
        <xsl:text>; </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>. </xsl:text>
      </xsl:otherwise>
    </xsl:choose>

  </xsl:template>


  <!-- ============================================================= -->
  <!--  56. Citation subparts (mode "none" separately at end)        -->
  <!-- ============================================================= -->

  <!-- names -->

  <xsl:template match="name" mode="nscitation">
    <xsl:value-of select="surname"/>
    <xsl:text>, </xsl:text>
    <xsl:value-of select="given-names"/>
    <xsl:text></xsl:text>
  </xsl:template>


  <xsl:template match="name" mode="book">
    <xsl:variable name="nodetotal" select="count(../*)"/>
    <xsl:variable name="penult" select="count(../*)-1"/>
    <xsl:variable name="position" select="position()"/>

    <xsl:choose>

      <!-- if given-names -->
      <xsl:when test="given-names">
        <xsl:apply-templates select="surname"/>
        <xsl:text>, </xsl:text>
        <xsl:call-template name="firstnames">
          <xsl:with-param name="nodetotal" select="$nodetotal"/>
          <xsl:with-param name="position" select="$position"/>
          <xsl:with-param name="names" select="given-names"/>
          <xsl:with-param name="pgtype">
            <xsl:choose>
              <xsl:when test="parent::person-group[@person-group-type]">
                <xsl:value-of select="parent::person-group/@person-group-type"/>
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="'author'"/>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:with-param>
        </xsl:call-template>

        <xsl:if test="suffix">
          <xsl:text>, </xsl:text>
          <xsl:apply-templates select="suffix"/>
        </xsl:if>
      </xsl:when>

      <!-- if no given-names -->
      <xsl:otherwise>
        <xsl:apply-templates select="surname"/>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:choose>
      <!-- if have aff -->
      <xsl:when test="following-sibling::aff"/>

      <!-- if don't have aff -->
      <xsl:otherwise>
        <xsl:choose>

          <!-- if part of person-group -->
          <xsl:when test="parent::person-group/@person-group-type">
            <xsl:choose>

              <!-- if author -->
              <xsl:when test="parent::person-group/@person-group-type='author'">
                <xsl:choose>
                  <xsl:when test="$nodetotal=$position">. </xsl:when>
                  <xsl:when test="$penult=$position">
                    <xsl:choose>
                      <xsl:when test="following-sibling::etal">, </xsl:when>
                      <xsl:otherwise>; </xsl:otherwise>
                    </xsl:choose>
                  </xsl:when>
                  <xsl:otherwise>; </xsl:otherwise>
                </xsl:choose>
              </xsl:when>

              <!-- if not author -->
              <xsl:otherwise>
                <xsl:choose>
                  <xsl:when test="$nodetotal=$position"/>
                  <xsl:when test="$penult=$position">
                    <xsl:choose>
                      <xsl:when test="following-sibling::etal">, </xsl:when>
                      <xsl:otherwise>; </xsl:otherwise>
                    </xsl:choose>
                  </xsl:when>
                  <xsl:otherwise>; </xsl:otherwise>
                </xsl:choose>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:when>

          <!-- if not part of person-group -->
          <xsl:otherwise>
            <xsl:choose>
              <xsl:when test="$nodetotal=$position">. </xsl:when>
              <xsl:when test="$penult=$position">
                <xsl:choose>
                  <xsl:when test="following-sibling::etal">, </xsl:when>
                  <xsl:otherwise>; </xsl:otherwise>
                </xsl:choose>
              </xsl:when>
              <xsl:otherwise>; </xsl:otherwise>
            </xsl:choose>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>

    </xsl:choose>
  </xsl:template>


  <xsl:template match="collab" mode="book">
    <xsl:apply-templates/>
    <xsl:if test="@collab-type='compilers'">
      <xsl:text>, </xsl:text>
      <xsl:value-of select="@collab-type"/>
    </xsl:if>
    <xsl:if test="@collab-type='assignee'">
      <xsl:text>, </xsl:text>
      <xsl:value-of select="@collab-type"/>
    </xsl:if>
    <xsl:text>. </xsl:text>
  </xsl:template>

  <xsl:template match="etal" mode="book">
    <xsl:text>et al.</xsl:text>
    <xsl:choose>
      <xsl:when test="parent::person-group/@person-group-type">
        <xsl:choose>
          <xsl:when test="parent::person-group/@person-group-type='author'">
            <xsl:text> </xsl:text>
          </xsl:when>
          <xsl:otherwise/>
        </xsl:choose>
      </xsl:when>

      <xsl:otherwise>
        <xsl:text> </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <!-- affiliations -->

  <xsl:template match="aff" mode="book">
    <xsl:variable name="nodetotal" select="count(../*)"/>
    <xsl:variable name="position" select="position()"/>

    <xsl:text> (</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>)</xsl:text>

    <xsl:choose>
      <xsl:when test="$nodetotal=$position">. </xsl:when>
      <xsl:otherwise>, </xsl:otherwise>
    </xsl:choose>
  </xsl:template>



  <!-- publication info -->

  <xsl:template match="article-title" mode="nscitation">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="uri" mode="nscitation">
    <a href="{self::uri}" target="_blank">
      <xsl:apply-templates/>
    </a>
  </xsl:template>

  <xsl:template match="article-title" mode="book">
    <xsl:apply-templates/>

    <xsl:choose>
      <xsl:when test="../fpage or ../lpage">
        <xsl:text>; </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>. </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="article-title" mode="editedbook">
    <xsl:apply-templates/>
    <xsl:text>. </xsl:text>
  </xsl:template>

  <xsl:template match="article-title" mode="conf">
    <xsl:apply-templates/>
    <xsl:choose>
      <xsl:when test="../conf-name">
        <xsl:text>. </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>; </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="article-title" mode="inconf">
    <xsl:apply-templates/>
    <xsl:text>. </xsl:text>
  </xsl:template>



  <xsl:template match="source" mode="nscitation">
    <em>
      <xsl:apply-templates/>
    </em>
  </xsl:template>

  <xsl:template match="ext-link" mode="nscitation">
    <a>
      <xsl:attribute name="href">
        <xsl:choose>
            <xsl:when test="starts-with(@xlink:href, 'www.')">
              <xsl:value-of select="concat('http://', @xlink:href)"/>
            </xsl:when>
            <xsl:when test="starts-with(@xlink:href, 'doi:')">
              <xsl:value-of select="concat('http://dx.doi.org/', substring-after(@xlink:href, 'doi:'))"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="@xlink:href"/>
            </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      <xsl:attribute name="target"><xsl:value-of select="'_blank'"/></xsl:attribute>
      <xsl:apply-templates/>
    </a>
  </xsl:template>

  <xsl:template match="source" mode="book">
    <xsl:choose>

      <xsl:when test="../trans-source">
        <xsl:apply-templates/>
        <xsl:choose>
          <xsl:when test="../volume | ../edition">
            <xsl:text>. </xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text> </xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>

      <xsl:otherwise>
        <xsl:apply-templates/>
        <xsl:text>. </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="source" mode="conf">
    <xsl:apply-templates/>
    <xsl:text>; </xsl:text>
  </xsl:template>

  <xsl:template match="trans-source" mode="book">
    <xsl:text> [</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>]. </xsl:text>
  </xsl:template>

  <xsl:template match="volume" mode="nscitation">
    <xsl:text> </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="volume | edition" mode="book">
    <xsl:apply-templates/>
    <xsl:if test="@collab-type='compilers'">
      <xsl:text>, </xsl:text>
      <xsl:value-of select="@collab-type"/>
    </xsl:if>
    <xsl:if test="@collab-type='assignee'">
      <xsl:text>, </xsl:text>
      <xsl:value-of select="@collab-type"/>
    </xsl:if>
    <xsl:text>. </xsl:text>
  </xsl:template>

  <!-- dates -->

  <xsl:template match="month" mode="nscitation">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="month" mode="book">
    <xsl:variable name="month" select="."/>
    <xsl:choose>
      <xsl:when test="$month='01' or $month='1' or $month='January'">Jan</xsl:when>
      <xsl:when test="$month='02' or $month='2' or $month='February'">Feb</xsl:when>
      <xsl:when test="$month='03' or $month='3' or $month='March'">Mar</xsl:when>
      <xsl:when test="$month='04' or $month='4' or $month='April'">Apr</xsl:when>
      <xsl:when test="$month='05' or $month='5' or $month='May'">May</xsl:when>
      <xsl:when test="$month='06' or $month='6' or $month='June'">Jun</xsl:when>
      <xsl:when test="$month='07' or $month='7' or $month='July'">Jul</xsl:when>
      <xsl:when test="$month='08' or $month='8' or $month='August'">Aug</xsl:when>
      <xsl:when test="$month='09' or $month='9' or $month='September'">Sep</xsl:when>
      <xsl:when test="$month='10' or $month='October'">Oct</xsl:when>
      <xsl:when test="$month='11' or $month='November'">Nov</xsl:when>
      <xsl:when test="$month='12' or $month='December'">Dec</xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$month"/>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:if test="../day">
      <xsl:text> </xsl:text>
      <xsl:value-of select="../day"/>
    </xsl:if>

    <xsl:choose>
      <xsl:when test="../time-stamp">
        <xsl:text>, </xsl:text>
        <xsl:value-of select="../time-stamp"/>
        <xsl:text> </xsl:text>
      </xsl:when>
      <xsl:when test="../access-date"/>
      <xsl:otherwise>
        <xsl:text>. </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="day" mode="nscitation">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="year" mode="nscitation">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="year" mode="book">
    <xsl:choose>
      <xsl:when test="../month or ../season or ../access-date">
        <xsl:apply-templates/>
        <xsl:text> </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
        <xsl:text>. </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>



  <xsl:template match="time-stamp" mode="nscitation">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="time-stamp" mode="book"/>


  <xsl:template match="access-date" mode="nscitation">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="access-date" mode="book">
    <xsl:text> [</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>]. </xsl:text>
  </xsl:template>



  <xsl:template match="season" mode="book">
    <xsl:apply-templates/>
    <xsl:if test="@collab-type='compilers'">
      <xsl:text>, </xsl:text>
      <xsl:value-of select="@collab-type"/>
    </xsl:if>
    <xsl:if test="@collab-type='assignee'">
      <xsl:text>, </xsl:text>
      <xsl:value-of select="@collab-type"/>
    </xsl:if>
    <xsl:text>. </xsl:text>
  </xsl:template>



  <!-- pages -->

  <xsl:template match="fpage" mode="nscitation">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="fpage" mode="book">
    <xsl:text>p. </xsl:text>
    <xsl:apply-templates/>

    <xsl:if test="../lpage">
      <xsl:text>.</xsl:text>
    </xsl:if>

  </xsl:template>


  <xsl:template match="lpage" mode="book">
    <xsl:choose>
      <xsl:when test="../fpage">
        <xsl:text>-</xsl:text>
        <xsl:apply-templates/>
        <xsl:text>.</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
        <xsl:text> p.</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="lpage" mode="nscitation">
    <xsl:apply-templates/>
  </xsl:template>

  <!-- misc stuff -->

  <xsl:template match="pub-id" mode="nscitation">
    <xsl:variable name="pub-id-type" select="@pub-id-type"/>
    <xsl:choose>
      <!-- Handle identifier as URL -->
      <xsl:when test="starts-with(current(), 'http')">
        <xsl:value-of select="@pub-id-type"/>
        <xsl:text>:&#160;</xsl:text>
        <a href="{current()}" target="_blank">
        <xsl:apply-templates/>
        </a>
      </xsl:when>
      <!-- Handle identifier as DOI but not URL -->
      <xsl:when test="$pub-id-type='doi'">
        <xsl:text>&#160;</xsl:text>
        <a href="https://doi.org/{current()}" target="_blank">
          <xsl:text>http://doi.org/</xsl:text>
          <xsl:apply-templates/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text> [</xsl:text>
        <xsl:value-of select="@pub-id-type"/>
        <xsl:text>: </xsl:text>
        <xsl:apply-templates/>
        <xsl:text>]</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="annotation" mode="nscitation">
    <blockquote>
      <xsl:apply-templates/>
    </blockquote>
  </xsl:template>

  <xsl:template match="comment" mode="nscitation">
      <xsl:apply-templates/>
      <xsl:apply-templates select="ext-link" mode="nscitation"/>
  </xsl:template>

  <xsl:template match="conf-name | conf-date" mode="conf">
    <xsl:apply-templates/>
    <xsl:text>; </xsl:text>
  </xsl:template>

  <xsl:template match="conf-loc" mode="conf">
    <xsl:apply-templates/>
    <xsl:text>. </xsl:text>
  </xsl:template>


  <!-- All formatting elements in citations processed normally -->
  <xsl:template match="bold | italic | monospace | overline | sc | strike | sub |sup | underline" mode="nscitation">
    <xsl:apply-templates select="."/>
  </xsl:template>

  <xsl:template match="bold | italic | monospace | overline | sc | strike | sub |sup | underline" mode="none">
    <xsl:apply-templates select="."/>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  "firstnames"                                                 -->
  <!-- ============================================================= -->

  <!-- called by match="name" in book mode,
     as part of citation handling
     when given-names is not all-caps -->

  <xsl:template name="firstnames">
    <xsl:param name="nodetotal"/>
    <xsl:param name="position"/>
    <xsl:param name="names"/>
    <xsl:param name="pgtype"/>

    <xsl:variable name="length" select="string-length($names)-1"/>
    <xsl:variable name="gnm" select="substring($names,$length,2)"/>
    <xsl:variable name="GNM">
      <xsl:call-template name="capitalize">
        <xsl:with-param name="str" select="substring($names,$length,2)"/>
      </xsl:call-template>
    </xsl:variable>

    <!--
<xsl:text>Value of $names = [</xsl:text><xsl:value-of select="$names"/><xsl:text>]</xsl:text>
<xsl:text>Value of $length = [</xsl:text><xsl:value-of select="$length"/><xsl:text>]</xsl:text>
<xsl:text>Value of $gnm = [</xsl:text><xsl:value-of select="$gnm"/><xsl:text>]</xsl:text>
<xsl:text>Value of $GNM = [</xsl:text><xsl:value-of select="$GNM"/><xsl:text>]</xsl:text>
-->

    <xsl:if test="$names">
      <xsl:choose>

        <xsl:when test="$gnm=$GNM">
          <xsl:apply-templates select="$names"/>
          <xsl:choose>
            <xsl:when test="$nodetotal!=$position">
              <xsl:text>.</xsl:text>
            </xsl:when>
            <xsl:when test="$pgtype!='author'">
              <xsl:text>.</xsl:text>
            </xsl:when>
          </xsl:choose>
        </xsl:when>

        <xsl:otherwise>
          <xsl:apply-templates select="$names"/>
        </xsl:otherwise>

      </xsl:choose>
    </xsl:if>

  </xsl:template>



  <!-- ============================================================= -->
  <!-- mode=none                                                     -->
  <!-- ============================================================= -->

  <!-- This mode assumes no punctuation is provided in the XML.
     It is used, among other things, for the citation/ref
     when there is no significant text node inside the ref.        -->
  <xsl:template match="name" mode="none">
    <xsl:choose>
      <xsl:when test="parent::person-group[@person-group-type='translator']">
        <xsl:choose>
          <xsl:when test="not(preceding-sibling::name)">
            <xsl:value-of select="surname"/>
            <xsl:text>, </xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="surname"/>
            <xsl:text>, </xsl:text>
          </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="given-names"/>
        <xsl:choose>
          <xsl:when test="not(following-sibling::name)">
            <xsl:text> (trans.), </xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>, </xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:when test="parent::person-group[@person-group-type='editor']">
        <xsl:choose>
          <xsl:when test="not(preceding-sibling::name)">
            <xsl:value-of select="surname"/>
            <xsl:text>, </xsl:text>
          </xsl:when>
        <xsl:otherwise>
        <xsl:value-of select="surname"/>
        <xsl:text>, </xsl:text>
        <xsl:value-of select="given-names"/>
        <xsl:choose>
          <xsl:when test="not(following-sibling::name)">
            <xsl:text> </xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>; </xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="given-names"/>
        <xsl:choose>
          <xsl:when test="not(following-sibling::name)">
            <xsl:text> (ed</xsl:text>
            <xsl:if test="following-sibling::name | preceding-sibling::name">s</xsl:if>
            <xsl:text>.), </xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:choose>
            <xsl:when test="count(preceding-sibling::name) = 1">
            <xsl:text> and </xsl:text>
            </xsl:when>
            <xsl:otherwise>
            <xsl:text>, </xsl:text>
            </xsl:otherwise>
            </xsl:choose>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="surname"/>
        <xsl:text>, </xsl:text>
        <xsl:value-of select="given-names"/>
        <xsl:choose>
          <xsl:when test="not(following-sibling::name)">
            <xsl:text> </xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>; </xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>


  <xsl:template match="uri" mode="none">
    <xsl:text> </xsl:text>
    <a href="{self::uri}" target="_blank">
      <xsl:apply-templates/>
    </a>
  </xsl:template>

  <xsl:template match="uri">
    <xsl:text> </xsl:text>
    <a href="{self::uri}" target="_blank">
      <xsl:apply-templates/>
    </a>
  </xsl:template>

  <xsl:template match="article-title" mode="none">
    <xsl:apply-templates/>
    <xsl:if test="../trans-title">
      <xsl:text>. </xsl:text>
    </xsl:if>
    <xsl:text>.&#160;</xsl:text>
  </xsl:template>

  <xsl:template match="chapter-title" mode="none">
    <xsl:text></xsl:text>
  </xsl:template>

  <xsl:template match="volume" mode="none">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="edition" mode="none">
    <xsl:choose>
      <xsl:when test="parent::element-citation[@publication-type='database']">
        <xsl:apply-templates/>
        <xsl:text>. </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
        <xsl:text> </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="supplement" mode="none">
    <xsl:text> </xsl:text>
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="issue" mode="none">
    <xsl:text>(</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>)</xsl:text>
  </xsl:template>

  <xsl:template match="publisher-loc" mode="none">
    <xsl:if test="not(preceding-sibling::publisher-name)">
    <xsl:apply-templates/>
    <xsl:text>: </xsl:text>
    </xsl:if>
  </xsl:template>

  <xsl:template match="conf-name" mode="none">
    <xsl:apply-templates/>
    <xsl:text>. </xsl:text>
  </xsl:template>

  <xsl:template match="conf-date" mode="none">
    <xsl:apply-templates/>
    <xsl:text>, </xsl:text>
  </xsl:template>

  <xsl:template match="conf-loc" mode="none">
    <xsl:apply-templates/>
  </xsl:template>


  <xsl:template match="publisher-name" mode="none">
    <xsl:choose>
    <xsl:when test="not(following-sibling::publisher-loc)">
        <xsl:apply-templates/>
    </xsl:when>
    <xsl:otherwise>
        <xsl:value-of select="following-sibling::publisher-loc"/>
        <xsl:text>: </xsl:text>
        <xsl:apply-templates/>
    </xsl:otherwise>
    </xsl:choose>
    <xsl:choose>
      <xsl:when test="following-sibling::fpage">
        <xsl:text>, </xsl:text>
      </xsl:when>

      <xsl:otherwise>
        <xsl:choose>
          <xsl:when test="following-sibling::pub-id[@pub-id-type='doi']">
            <xsl:text>, </xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>. </xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="person-group" mode="none">
    <xsl:variable name="gnms" select="string(descendant::given-names)"/>
    <xsl:variable name="GNMS">
      <xsl:call-template name="capitalize">
        <xsl:with-param name="str" select="$gnms"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:choose>
      <xsl:when test="$gnms=$GNMS">
        <xsl:apply-templates/>
            <xsl:if test="not(preceding-sibling::person-group)">
            <xsl:text>(</xsl:text>
            <xsl:value-of select="..//year"/>
            <xsl:text>).</xsl:text>
            </xsl:if>
      </xsl:when>

      <xsl:otherwise>
        <xsl:choose>
          <xsl:when test="self::person-group/@person-group-type='author'">
            <strong>
              <xsl:apply-templates select="node()" mode="none"/>
            </strong>
            <xsl:if test="not(preceding-sibling::person-group)">
            <xsl:text>. (</xsl:text>
            <xsl:value-of select="..//year"/>
            <xsl:text>).</xsl:text>
            </xsl:if>
          </xsl:when>
          <xsl:when test="self::person-group/@person-group-type='editor'">
            <strong>
              <xsl:apply-templates select="node()" mode="none"/>
            </strong>
            <xsl:if test="not(preceding-sibling::person-group)">
            <xsl:text>. (</xsl:text>
            <xsl:value-of select="..//year"/>
            <xsl:text>).</xsl:text>
            </xsl:if>
          </xsl:when>
          <xsl:otherwise>
            <xsl:apply-templates select="node()" mode="none"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>


    <xsl:text>&#160;</xsl:text>
    <xsl:choose>
      <xsl:when test="self::person-group/@person-group-type='author'">
        <xsl:if test="../chapter-title">
          <xsl:value-of select="../chapter-title"/>
          <xsl:text>&#160;In:&#160;</xsl:text>
        </xsl:if>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="collab" mode="none">
    <strong>

      <xsl:apply-templates/>
    </strong>
    <xsl:if test="@collab-type">
      <xsl:text>, </xsl:text>
      <xsl:value-of select="@collab-type"/>
    </xsl:if>

    <xsl:choose>
      <xsl:when test="following-sibling::collab">
        <xsl:text>; </xsl:text>
      </xsl:when>

      <xsl:otherwise>
        <xsl:text>. </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="source" mode="none">
    <xsl:choose>
      <xsl:when test="parent::element-citation[@publication-type='thesis']">
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:when test="parent::element-citation[@publication-type='webpage']">
        <xsl:apply-templates/>
      </xsl:when>
      <xsl:otherwise>
        <em>
          <xsl:apply-templates/>
        </em>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:choose>
      <xsl:when test="following-sibling::edition">
        <xsl:text>. </xsl:text>
      </xsl:when>
      <xsl:when test="following-sibling::publisher-name">
        <xsl:text>. </xsl:text>
      </xsl:when>
      <xsl:when test="following-sibling::volume">
        <xsl:text> </xsl:text>
      </xsl:when>
      <xsl:when test="following-sibling::issue">
        <xsl:text> </xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>, </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
    <!-- <xsl:choose>
      <xsl:when test="../access-date">
        <xsl:if test="../edition">
          <xsl:text> </xsl:text>
          <xsl:apply-templates select="../edition" mode="plain"/>
          <xsl:text></xsl:text>
        </xsl:if>
        <xsl:text>. </xsl:text>
      </xsl:when>

      <xsl:when test="../volume | ../fpage">
        <xsl:if test="../edition">
          <xsl:text> </xsl:text>
          <xsl:apply-templates select="../edition" mode="plain"/>
          <xsl:text></xsl:text>
        </xsl:if>
        <xsl:text> </xsl:text>
      </xsl:when>

      <xsl:otherwise>
        <xsl:if test="../edition">
          <xsl:text> </xsl:text>
          <xsl:apply-templates select="../edition" mode="plain"/>
          <xsl:text> ed</xsl:text>
        </xsl:if>
        <xsl:text>. </xsl:text>
      </xsl:otherwise>
    </xsl:choose> -->
  </xsl:template>

  <xsl:template match="trans-title" mode="none">
    <xsl:text> [</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>]. </xsl:text>
  </xsl:template>

  <xsl:template match="month" mode="none">
    <xsl:variable name="month" select="."/>
    <xsl:choose>
      <xsl:when test="$month='01' or $month='1' ">Jan</xsl:when>
      <xsl:when test="$month='02' or $month='2' ">Feb</xsl:when>
      <xsl:when test="$month='03' or $month='3' ">Mar</xsl:when>
      <xsl:when test="$month='04' or $month='4' ">Apr</xsl:when>
      <xsl:when test="$month='05' or $month='5' ">May</xsl:when>
      <xsl:when test="$month='06' or $month='6'">Jun</xsl:when>
      <xsl:when test="$month='07' or $month='7'">Jul</xsl:when>

      <xsl:when test="$month='08' or $month='8' ">Aug</xsl:when>
      <xsl:when test="$month='09' or $month='9' ">Sep</xsl:when>
      <xsl:when test="$month='10' ">Oct</xsl:when>
      <xsl:when test="$month='11' ">Nov</xsl:when>
      <xsl:when test="$month='12' ">Dec</xsl:when>

      <xsl:otherwise>
        <xsl:value-of select="$month"/>
      </xsl:otherwise>
    </xsl:choose>

    <xsl:if test="../day">
      <xsl:text> </xsl:text>
      <xsl:value-of select="../day"/>
    </xsl:if>

    <xsl:if test="../year">
      <xsl:text> </xsl:text>
      <xsl:value-of select="../year"/>
    </xsl:if>

  </xsl:template>

  <xsl:template match="day" mode="none"/>

  <xsl:template match="year" mode="none">
    <!--
    <xsl:choose>
      <xsl:when test="../month or ../season or ../access-date">
        <xsl:apply-templates mode="none"/>
        <xsl:text> </xsl:text>
      </xsl:when>

      <xsl:otherwise>
        <xsl:apply-templates mode="none"/>
        <xsl:if test="../volume or ../issue">
          <xsl:text>;</xsl:text>
        </xsl:if>
      </xsl:otherwise>
    </xsl:choose>
    -->
  </xsl:template>

  <xsl:template match="access-date" mode="none">
    <xsl:text> [</xsl:text>
    <xsl:apply-templates/>
    <xsl:text>];</xsl:text>
  </xsl:template>

  <xsl:template match="season" mode="none">
    <xsl:apply-templates/>
    <xsl:text>;</xsl:text>
  </xsl:template>

  <xsl:template match="fpage" mode="none">
    <xsl:variable name="fpgct" select="count(../fpage)"/>
    <xsl:variable name="lpgct" select="count(../lpage)"/>
    <xsl:variable name="hermano" select="name(following-sibling::node())"/>
    <xsl:choose>
      <xsl:when test="preceding-sibling::fpage">
        <xsl:choose>
          <xsl:when test="following-sibling::fpage">
            <xsl:text> </xsl:text>
            <xsl:apply-templates/>

            <xsl:if test="$hermano='lpage'">
              <xsl:text>&#8211;</xsl:text>
              <xsl:apply-templates select="following-sibling::lpage[1]" mode="none"/>
            </xsl:if>
            <xsl:text>,</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text> </xsl:text>
            <xsl:apply-templates/>
            <xsl:if test="$hermano='lpage'">
              <xsl:text>&#8211;</xsl:text>
              <xsl:apply-templates select="following-sibling::lpage[1]" mode="none"/>
            </xsl:if>
            <xsl:text>.</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <xsl:choose>
          <xsl:when test="preceding-sibling::publisher-name">
            <xsl:choose>
              <xsl:when test="following-sibling::lpage[1]">
                <xsl:text>pp. </xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>p. </xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:when>
          <xsl:when test="parent::element-citation[@publication-type='newspaper']">
            <xsl:choose>
              <xsl:when test="following-sibling::lpage[1]">
                <xsl:text>, pp. </xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>, p. </xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:when>
          <xsl:when test="parent::element-citation[@publication-type='conf-proc']">
            <xsl:choose>
              <xsl:when test="following-sibling::lpage[1]">
                <xsl:text>, pp. </xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>, p. </xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:when>

          <xsl:otherwise>
            <xsl:text>: </xsl:text>
          </xsl:otherwise>
        </xsl:choose>
        <xsl:apply-templates/>
        <xsl:choose>
          <xsl:when test="$hermano='lpage'">
            <xsl:text>&#8211;</xsl:text>
            <xsl:apply-templates select="following-sibling::lpage[1]" mode="write"/>
            <xsl:choose>
              <xsl:when test="following-sibling::pub-id[@pub-id-type='doi']">
                <xsl:text>, </xsl:text>
              </xsl:when>
              <xsl:otherwise>
                <xsl:text>. </xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:when>
          <xsl:when test="$hermano='fpage'">
            <xsl:text>,</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>.</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="lpage" mode="none"/>

  <xsl:template match="lpage" mode="write">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="gov" mode="none">
    <xsl:choose>
      <xsl:when test="../trans-title">
        <xsl:apply-templates/>
      </xsl:when>

      <xsl:otherwise>
        <xsl:apply-templates/>
          <xsl:text>. </xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="patent" mode="none">
    <xsl:apply-templates/>
    <xsl:text>. </xsl:text>
  </xsl:template>

  <xsl:template match="pub-id[@pub-id-type='doi']" mode="none">
    <xsl:text>DOI:&#160;</xsl:text>
      <a href="http://dx.doi.org/{current()}" target="_blank">
      <xsl:text>http://dx.doi.org/</xsl:text>
      <xsl:apply-templates/>
    </a>
  </xsl:template>

  <xsl:template match="pub-id[@pub-id-type='pmid']" mode="none"> [<a href="http://www.ncbi.nlm.nih.gov/pubmed/{current()}" target="_blank">
      <xsl:text>PubMed</xsl:text>
    </a>]
  </xsl:template>

  <xsl:template match="pub-id" mode="none">
    <xsl:text> [</xsl:text>
    <span class="pub-id-type-{@pub-id-type}">
      <xsl:value-of select="@pub-id-type"/>
    </span>
    <xsl:text>: </xsl:text>
      <xsl:apply-templates/>
    <xsl:text>]</xsl:text>
  </xsl:template>

  <xsl:template match="comment" mode="none">
    <xsl:text> </xsl:text>
    <xsl:apply-templates/>
    <xsl:text>.</xsl:text>
  </xsl:template>


  <!-- ============================================================= -->
  <!--  57. "CITATION-TAG-ENDS"                                      -->
  <!-- ============================================================= -->


  <xsl:template name="citation-tag-ends">

    <xsl:apply-templates select="series" mode="citation"/>

    <!-- If language is not English -->
    <!-- XX review logic -->
    <xsl:if test="article-title[@xml:lang!='en']
               or article-title[@xml:lang!='EN']">
    </xsl:if>

    <xsl:apply-templates select="comment" mode="citation"/>

    <xsl:apply-templates select="annotation" mode="citation"/>

  </xsl:template>

      <xsl:template name="capitalize">
    <xsl:param name="str"/>
    <xsl:value-of
      select="translate($str,
                          'abcdefghjiklmnopqrstuvwxyz',
                          'ABCDEFGHJIKLMNOPQRSTUVWXYZ')"
    />
  </xsl:template>

    <!-- START video handling -->

    <xsl:template match="media">
        <xsl:variable name="data-doi" select="child::object-id[@pub-id-type='doi']/text()"/>
        <xsl:choose>
            <!-- Handle Video Media-->
            <xsl:when test="@mimetype = 'video'">
              <xsl:choose>
                <!-- Embed Vimeo -->
                <xsl:when test="contains(./@xlink:href, 'player.vimeo.com')">
                  <div class="media" data-doi="{$data-doi}">
                    <xsl:apply-templates select="." mode="vimeo"/>
                  </div>
                </xsl:when>

                <!-- Embed Youtube -->
                <xsl:when test="contains(./@xlink:href, 'youtube.com')">
                  <div class="media" data-doi="{$data-doi}">
                    <xsl:apply-templates select="." mode="youtube"/>
                  </div>
                </xsl:when>
                <xsl:when test="contains(./@xlink:href, 'youtu.be')">
                  <div class="media" data-doi="{$data-doi}">
                    <xsl:apply-templates select="." mode="youtube"/>
                  </div>
                </xsl:when>
                <xsl:otherwise>
                  <a href="{@xlink:href}">Video URL</a>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:when>

            <!-- Handle Audio Media-->
            <xsl:when test="@mimetype = 'audio'">
              <xsl:choose>
                <xsl:when test="contains(./@xlink:href, 'soundcloud.com/player')">
                  <div class="media" data-doi="{$data-doi}">
                    <xsl:apply-templates select="." mode="soundcloud"/>
                  </div>
                </xsl:when>
                <xsl:otherwise>
                  <a href="{@xlink:href}">Video URL</a>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:when>

            <xsl:otherwise>
            <!-- MSL: I think this is test code that doesn't do much -->
              <xsl:apply-templates select="." mode="testing"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- media caption -->
    <xsl:template match="media/caption">
        <div class="media-caption">
            <span class="media-label">
                <xsl:value-of select="preceding-sibling::label"/>
            </span>
            <xsl:text> </xsl:text>

            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="media/caption/title">
        <span class="caption-title">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <!-- END video handling -->

    <!-- START sub-article -->

    <xsl:template match="sub-article">
        <xsl:variable name="data-doi" select="child::front-stub/article-id[@pub-id-type='doi']/text()"/>
        <div data-doi="{$data-doi}">
            <!-- determine the attribute -->
            <xsl:attribute name="id">
                <xsl:if test="@article-type='article-commentary'">
                    <xsl:text>decision-letter</xsl:text>
                </xsl:if>
                <xsl:if test="@article-type='reply'">
                    <xsl:text>author-response</xsl:text>
                </xsl:if>
            </xsl:attribute>
            <xsl:apply-templates/>

        </div>
        <div class="panel-separator"></div>
    </xsl:template>

    <!-- sub-article body -->
    <xsl:template match="sub-article/body">
        <div>
            <xsl:attribute name="class">
                <xsl:if test="../@article-type='article-commentary'">
                    <xsl:text>janeway-article-decision-letter</xsl:text>
                </xsl:if>
                <xsl:if test="../@article-type='reply'">
                    <xsl:text>janeway-article-author-response</xsl:text>
                </xsl:if>
            </xsl:attribute>
            <div class="article fulltext-view">
                <xsl:apply-templates/>
            </div>
        </div>
        <div>
            <xsl:attribute name="class">
                <xsl:if test="../@article-type='article-commentary'">
                    <xsl:text>janeway-article-decision-letter-doi</xsl:text>
                </xsl:if>
                <xsl:if test="../@article-type='reply'">
                    <xsl:text>janeway-article-author-response-doi</xsl:text>
                </xsl:if>
            </xsl:attribute>
            <strong>DOI:</strong>
            <xsl:text> </xsl:text>

            <xsl:variable name="doino" select="preceding-sibling::*//article-id"/>
            <a>
                <xsl:attribute name="href">
                    <xsl:value-of select="concat('/lookup/doi/', $doino)"/>
                </xsl:attribute>
                <xsl:value-of select="concat('http://dx.doi.org/', $doino)"/>
            </a>
        </div>
    </xsl:template>

    <!-- START sub-article author contrib information -->

    <xsl:template match="sub-article//contrib-group">
        <div class="acta-article-editors">
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="sub-article//contrib-group/contrib">
        <div>
            <xsl:attribute name="class">
                <xsl:value-of select="concat('acta-article-decision-reviewing', @contrib-type)"/>
            </xsl:attribute>
            <xsl:apply-templates/>
        </div>
    </xsl:template>

    <xsl:template match="contrib[@contrib-type='editor']/name/given-names | contrib[@contrib-type='editor']/name/surname">
        <span class="nlm-given-names">
            <xsl:value-of select="given-names"/>
        </span>
        <xsl:text> </xsl:text>
        <span class="nlm-surname">
            <xsl:value-of select="surname"/>
        </span>
        <xsl:if test="parent::suffix">
            <xsl:text> </xsl:text>
            <span class="nlm-surname">
                <xsl:value-of select="parent::suffix"/>
            </span>
        </xsl:if>
        <xsl:text>, </xsl:text>
    </xsl:template>

    <xsl:template match="contrib[@contrib-type='editor']//aff">
        <xsl:apply-templates select="child::*"/>
    </xsl:template>

    <xsl:template match="contrib[@contrib-type='editor']//role | contrib[@contrib-type='editor']//institution | contrib[@contrib-type='editor']//country">
        <span class="nlm-{name()}">
            <xsl:apply-templates/>
        </span>
        <xsl:if test="not(parent::aff) or (parent::aff and following-sibling::*)">
            <xsl:text>, </xsl:text>
        </xsl:if>
    </xsl:template>

    <!-- END sub-article author contrib information -->

    <!-- box text -->
    <xsl:template match="boxed-text">
        <xsl:variable name="data-doi" select="child::object-id[@pub-id-type='doi']/text()"/>
        <xsl:choose>
            <xsl:when test="$data-doi != ''">
                <div class="boxed-text">
                    <xsl:attribute name="data-doi">
                        <xsl:value-of select="$data-doi"/>
                    </xsl:attribute>
                    <xsl:apply-templates select="." mode="testing"/>
                </div>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates select="." mode="testing"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="boxed-text/label">
        <span class="boxed-text-label">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="inline-graphic">
        <xsl:variable name="graphics" select="./@xlink:href"/>
        <xsl:variable name="ig-variant">
            <xsl:choose>
                <xsl:when test="//article/@article-type = 'research-article'">
                    <xsl:value-of select="'research-'"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'nonresearch-'"/>
                </xsl:otherwise>
            </xsl:choose>
            <xsl:choose>
                <xsl:when test="ancestor::boxed-text">
                    <xsl:value-of select="'box'"/>
                </xsl:when>
                <xsl:when test="ancestor::fig">
                    <xsl:value-of select="'fig'"/>
                </xsl:when>
                <xsl:when test="ancestor::table-wrap">
                    <xsl:value-of select="'table'"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="'other'"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <img src="{$graphics}" class="responsive-img" />
    </xsl:template>

    <xsl:template match="bio//title">
        <h2>
            <xsl:value-of select="node()"/>
        </h2>
    </xsl:template>

    <xsl:template name="appendices-main-text">
        <xsl:apply-templates select="//back/app-group/app" mode="testing"/>
    </xsl:template>

    <xsl:template match="app">
        <div id="{@id}">
            <xsl:apply-templates />
        </div>
    </xsl:template>


    <xsl:template match="app//title">
      <xsl:choose>
        <xsl:when test="name(parent::*) = 'caption'" >
          <strong><xsl:value-of select="node()"/></strong>
        </xsl:when>
        <xsl:otherwise>
          <h2 id="{@id}">
            <xsl:if test="preceding-sibling::label">
              <xsl:value-of select="preceding-sibling::label"/>&#160;</xsl:if>
              <xsl:value-of select="node()"/>
          </h2>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:template>

    <xsl:template match="app//sec//title">
        <h3>
            <xsl:if test="preceding-sibling::label"><xsl:value-of select="preceding-sibling::label"/>&#160;</xsl:if>

        </h3>
    </xsl:template>


    <!-- START - general format -->

    <!-- list elements start-->

    <xsl:template match="list">
        <xsl:choose>
            <xsl:when test="@list-type = 'simple' or @list-type = 'bullet'">
                <ul>
                    <xsl:attribute name="class">
                        <xsl:choose>
                            <xsl:when test="@list-type = 'simple'">
                                <xsl:value-of select="'list-simple'"/>
                            </xsl:when>
                            <xsl:when test="@list-type = 'bullet'">
                                <xsl:value-of select="'list-unord'"/>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:attribute>
                    <xsl:apply-templates/>
                </ul>
            </xsl:when>
            <xsl:otherwise>
                <xsl:choose>
                    <xsl:when test="@list-type = 'order'">
                        <ol>
                            <xsl:attribute name="class">
                                <xsl:value-of select="'list-order'"/>
                            </xsl:attribute>

                            <xsl:if test="@continued-from">
                                <xsl:variable name="count-list-items">
                                  <xsl:number count="list-item"  from="list[@id=@continued-from]" level="any"/>
                                </xsl:variable>
                                <xsl:attribute name="start">
                                  <xsl:value-of select="$count-list-items + 1"/>
                                </xsl:attribute>
                            </xsl:if>
                            <xsl:apply-templates/>
                        </ol>
                    </xsl:when>
                    <xsl:when test="@list-type = 'gloss'">
                        <div class="gloss-wrapper">
                                <xsl:apply-templates/>
                        </div>
                    </xsl:when>
                    <xsl:when test="@list-type = 'wordfirst'">
                        <div class="gloss-header">
                            <ol class="gloss-word gloss-first">
                                <xsl:apply-templates/>
                            </ol>
                        </div>
                    </xsl:when>
                    <xsl:when test="@list-type = 'sentence-gloss'">
                        <div class="gloss-item">
                            <ol class="gloss-sentence">
                                <div style="clear:both;"></div>
                                <xsl:apply-templates/>
                            </ol>
                        </div>
                    </xsl:when>
                    <xsl:when test="@list-type = 'final-sentence'">
                        <ol class="gloss-sentence">
                            <xsl:apply-templates/>
                        </ol>
                    </xsl:when>
                    <xsl:when test="@list-type = 'word'">
                        <ol class="gloss-word">
                            <xsl:apply-templates/>
                        </ol>
                    </xsl:when>
                    <xsl:when test="@list-type = 'roman-lower'">
                        <ol>
                            <xsl:attribute name="class">
                                <xsl:value-of select="'list-romanlower'"/>
                            </xsl:attribute>
                            <xsl:apply-templates/>
                        </ol>
                    </xsl:when>
                    <xsl:when test="@list-type = 'roman-upper'">
                        <ol>
                            <xsl:attribute name="class">
                                <xsl:value-of select="'list-romanupper'"/>
                            </xsl:attribute>
                            <xsl:apply-templates/>
                        </ol>
                    </xsl:when>
                    <xsl:when test="@list-type = 'alpha-lower'">
                        <ol>
                            <xsl:attribute name="class">
                                <xsl:value-of select="'list-alphalower'"/>
                            </xsl:attribute>
                            <xsl:apply-templates/>
                        </ol>
                    </xsl:when>
                    <xsl:when test="@list-type = 'alpha-upper'">
                        <ol>
                            <xsl:attribute name="class">
                                <xsl:value-of select="'list-alphaupper'"/>
                            </xsl:attribute>
                            <xsl:apply-templates/>
                        </ol>
                    </xsl:when>
                </xsl:choose>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>



    <xsl:template match="list-item">
        <xsl:choose>
            <xsl:when test="not(parent::list[@list-type='gloss']) and not(parent::list[@list-type='sentence-gloss'])">
                <!-- Target list-items that have a title so we can use the title as the list-item-type -->
                <!-- See also match="title" where we handle wrapping the title in a span -->
                <xsl:choose>
                    <xsl:when test="name(*[1]) = 'title'">
                        <li class="no-list-type">
                            <xsl:apply-templates/>
                        </li>
                    </xsl:when>

                    <xsl:otherwise>
                        <li>
                            <xsl:apply-templates/>
                        </li>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:when>
            <!-- Glosses -->
            <xsl:when test="parent::list[@list-type='gloss'] and count(preceding-sibling::list-item) = 0">
                <ol class="gloss-sentence"><xsl:apply-templates/></ol>
            </xsl:when>
            <xsl:otherwise>
                <xsl:apply-templates/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="bold">
        <strong>
            <xsl:apply-templates/>
        </strong>
    </xsl:template>

    <xsl:template match="italic">
        <em>
            <xsl:apply-templates/>
        </em>
    </xsl:template>

    <xsl:template match="underline">
        <span class="underline">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="strike">
        <span class="strikethrough">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="monospace">
        <span class="monospace">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="sc">
        <span class="small-caps">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="styled-content">
        <span class="styled-content">
            <xsl:if test="@style">
                <xsl:attribute name="style">
                    <xsl:value-of select="@style"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="sup">
        <sup>
            <xsl:apply-templates/>
        </sup>
    </xsl:template>

    <xsl:template match="sub">
        <sub>
            <xsl:apply-templates/>
        </sub>
    </xsl:template>

    <xsl:template match="break">
        <br/>
    </xsl:template>

      <xsl:template match="verse-group">
        <pre>
          <xsl:apply-templates/>
        </pre>
      </xsl:template>

      <xsl:template match="verse-line">
        <xsl:apply-templates/>
      </xsl:template>

    <xsl:template match="title">
        <xsl:choose>
            <xsl:when test="name(parent::*) = 'list-item'">
                <span class="jats-list-type">
                    <xsl:value-of select="node()" />
                </span>
            </xsl:when>
            <xsl:otherwise>
                <strong>
                    <xsl:apply-templates/>
                </strong>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="disp-quote">
        <xsl:text disable-output-escaping="yes">&lt;blockquote class="disp-quote"&gt;</xsl:text>
            <xsl:apply-templates/>
        <xsl:text disable-output-escaping="yes">&lt;/blockquote&gt;</xsl:text>
    </xsl:template>


    <xsl:template match="attrib">
        <p class="jats-attrib">
            <xsl:apply-templates/>
        </p>
    </xsl:template>

    <xsl:template match="address">
        <span class="jats-addr">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="address/institution">
        <span class="jats-addr-institution">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="address/addr-line">
        <span class="jats-addr-line">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="address/country | address/phone | address/fax | address/email | address/uri">
        <span class="jats-addr-line-other">
            <xsl:apply-templates/>
        </span>
    </xsl:template>

    <xsl:template match="glossary/title">
        <h2>
            <xsl:apply-templates/>
        </h2>
    </xsl:template>

    <xsl:template match="def-item/term">
        <strong>
            <xsl:apply-templates/>
        </strong>
    </xsl:template>

    <xsl:template match="code">
        <xsl:choose>
            <xsl:when test="@xml:space = 'preserve'">
                <pre>
                    <code>
                        <xsl:apply-templates/>
                    </code>
                </pre>
            </xsl:when>
            <xsl:otherwise>
                <code>
                    <xsl:apply-templates/>
                </code>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- END - general format -->

    <xsl:template match="sub-article//title-group | sub-article/front-stub | fn-group[@content-type='competing-interest']/fn/p | //history//*[@publication-type='journal']/article-title">
        <xsl:apply-templates/>
    </xsl:template>

    <xsl:template match="caption | table-wrap/table | table-wrap-foot | fn | bold | italic | underline | monospace | styled-content | sub | sup | sec/title | ext-link | app/title | disp-formula | inline-formula | list | list-item | disp-quote | code" mode="testing">
        <xsl:apply-templates select="."/>
    </xsl:template>

    <!-- nodes to remove -->
    <xsl:template match="aff/label"/>
    <xsl:template match="app/label"/>
    <xsl:template match="fn/label"/>
    <xsl:template match="sec/label"/>
    <xsl:template match="disp-formula/label"/>
    <xsl:template match="fn-group[@content-type='competing-interest']/title"/>
    <xsl:template match="permissions/copyright-year | permissions/copyright-holder"/>
    <xsl:template match="fn-group[@content-type='author-contribution']/title"/>
    <xsl:template match="author-notes/fn[@fn-type='con']/label"/>
    <xsl:template match="author-notes/fn[@fn-type='other']/label"/>
    <xsl:template match="author-notes/corresp/label"/>
    <xsl:template match="abstract/title"/>
    <xsl:template match="ref/label"/>
    <xsl:template match="fig/graphic"/>
    <xsl:template match="fig-group//object-id | fig-group//graphic | fig//label"/>
    <xsl:template match="ack/title"/>
    <xsl:template match="ref//year | ref//article-title | ref//fpage | ref//volume | ref//source | ref//pub-id | ref//lpage | ref//comment | ref//supplement | ref//person-group[@person-group-type='editor'] | ref//edition | ref//publisher-loc | ref//publisher-name | ref//ext-link"/>
    <xsl:template match="person-group[@person-group-type='author']"/>
    <xsl:template match="media/label"/>
    <xsl:template match="sub-article//article-title"/>
    <xsl:template match="sub-article//article-id"/>
    <xsl:template match="object-id | table-wrap/label"/>
    <xsl:template match="funding-group//institution-wrap/institution-id"/>
    <xsl:template match="table-wrap/graphic"/>
    <xsl:template match="author-notes/fn[@fn-type='present-address']/label"/>
    <xsl:template match="author-notes/fn[@fn-type='deceased']/label"/>

    <xsl:template name="camel-case-word">
        <xsl:param name="text"/>
        <xsl:value-of select="translate(substring($text, 1, 1), $smallcase, $uppercase)" /><xsl:value-of select="translate(substring($text, 2, string-length($text)-1), $uppercase, $smallcase)" />
    </xsl:template>

    <xsl:template name="month-long">
        <xsl:param name="month"/>
        <xsl:variable name="month-int" select="number(month)"/>
        <xsl:choose>
            <xsl:when test="$month-int = 1">
                <xsl:value-of select="'January'"/>
            </xsl:when>
            <xsl:when test="$month-int = 2">
                <xsl:value-of select="'February'"/>
            </xsl:when>
            <xsl:when test="$month-int = 3">
                <xsl:value-of select="'March'"/>
            </xsl:when>
            <xsl:when test="$month-int = 4">
                <xsl:value-of select="'April'"/>
            </xsl:when>
            <xsl:when test="$month-int = 5">
                <xsl:value-of select="'May'"/>
            </xsl:when>
            <xsl:when test="$month-int = 6">
                <xsl:value-of select="'June'"/>
            </xsl:when>
            <xsl:when test="$month-int = 7">
                <xsl:value-of select="'July'"/>
            </xsl:when>
            <xsl:when test="$month-int = 8">
                <xsl:value-of select="'August'"/>
            </xsl:when>
            <xsl:when test="$month-int = 9">
                <xsl:value-of select="'September'"/>
            </xsl:when>
            <xsl:when test="$month-int = 10">
                <xsl:value-of select="'October'"/>
            </xsl:when>
            <xsl:when test="$month-int = 11">
                <xsl:value-of select="'November'"/>
            </xsl:when>
            <xsl:when test="$month-int = 12">
                <xsl:value-of select="'December'"/>
            </xsl:when>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="citation">
        <xsl:variable name="year"><xsl:call-template name="year"/></xsl:variable>
        <xsl:variable name="citationid"><xsl:call-template name="citationid"/></xsl:variable>
        <xsl:value-of select="concat(//journal-meta/journal-title-group/journal-title, ' ', $year, ';', $citationid)"/>
    </xsl:template>

    <xsl:template name="year">
        <xsl:choose>
            <xsl:when test="//article-meta/pub-date[@date-type='pub']/year">
                <xsl:value-of select="//article-meta/pub-date[@date-type='pub']/year"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="//article-meta/permissions/copyright-year"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template name="volume">
        <xsl:variable name="value">
            <xsl:choose>
                <xsl:when test="//article-meta/volume">
                    <xsl:value-of select="//article-meta/volume"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:variable name="year"><call-template name="year"/></xsl:variable>
                    <xsl:value-of select="$year - 2011"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>
        <xsl:value-of select="$value"/>
    </xsl:template>

    <xsl:template name="citationid">
        <xsl:variable name="volume"><xsl:call-template name="volume"/></xsl:variable>
        <xsl:choose>
            <xsl:when test="//article-meta/pub-date[@pub-type='collection']/year">
                <xsl:value-of select="concat($volume, ':', //article-meta/elocation-id)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="//article-meta/article-id[@pub-id-type='doi']"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

  <!-- ============================================================= -->
  <!--  TEI                                      -->
  <!-- ============================================================= -->


<xsl:template match="tei:body/tei:head"/>

  <xsl:template match="tei:teiHeader">
      <xsl:apply-templates select="tei:fileDesc" mode="pagehead"/>
  </xsl:template>

  <xsl:template mode="pagehead" match="tei:fileDesc">
    <xsl:apply-templates select="tei:titleStmt" mode="pagehead"/>
  </xsl:template>

  <xsl:template match="tei:titleStmt" mode="pagehead">

  </xsl:template>



  <xsl:template match="tei:body">
    <div class="article-body">
    <xsl:apply-templates/>

    <xsl:call-template name="ctpl_figure"/>

    <xsl:call-template name="ctpl_footnotes"/>
    </div>

  </xsl:template>

  <!--   DIVISIONS     -->
  <xsl:template match="tei:div">
    <xsl:choose>
      <!--Contact Details Box -->
      <!-- THIS IS WRONG, DOESN'T WORK IN HTML -->
      <xsl:when test="@type='box'">
        <address>
          <xsl:apply-templates/>
        </address>
      </xsl:when>
      <!--   Default  -->
      <xsl:otherwise>
        <!-- Creates anchor if there is @xml:id -->
        <xsl:if test="@xml:id">
          <a>
            <xsl:attribute name="id">
              <xsl:value-of select="@xml:id"/>
            </xsl:attribute>
            <xsl:text>&#160;</xsl:text>
          </a>
        </xsl:if>
         <div>
          <xsl:apply-templates/>
        </div>
      </xsl:otherwise>
    </xsl:choose>
    </xsl:template>
  <!--   HEADINGS     -->
  <xsl:template match="tei:TEI/*/*/tei:div/tei:head">
    <xsl:if test="parent::tei:div/@n"><h2 class="center"><xsl:value-of select="parent::tei:div/@n"/><xsl:text> </xsl:text></h2></xsl:if>
    <h2 id="{generate-id()}" class="center">
      <xsl:apply-templates/>
    </h2>
  </xsl:template>
  <xsl:template match="tei:TEI/*/*/tei:div/tei:div/tei:head">

    <h3 id="{generate-id()}"><xsl:if test="parent::tei:div/@n"><xsl:value-of select="parent::tei:div/@n"/><xsl:text> </xsl:text></xsl:if>
      <xsl:apply-templates/>
    </h3>
  </xsl:template>
  <xsl:template match="tei:TEI/*/*/tei:div/tei:div/tei:div/tei:head">
    <h4 id="{generate-id()}">
      <xsl:apply-templates/>
    </h4>
  </xsl:template>
  <xsl:template match="tei:TEI/*/*/tei:div/tei:div/tei:div/tei:div/tei:head">
    <h5 id="{generate-id()}">
      <xsl:apply-templates/>
    </h5>
  </xsl:template>
  <xsl:template match="tei:TEI/*/*/tei:div/tei:div/tei:div/tei:div/tei:div/tei:head">
    <h6 id="{generate-id()}">
      <xsl:apply-templates/>
    </h6>
  </xsl:template>
  <xsl:template match="tei:TEI/*/*/tei:div/tei:div/tei:div/tei:div/tei:div/tei:div/tei:head">
    <h6 id="{generate-id()}">
      <xsl:apply-templates/>
    </h6>
  </xsl:template>
  <!--   TOC     -->
  <xsl:template match="tei:body/tei:head" mode="toc">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="tei:note" mode="toc"> </xsl:template>
  <xsl:template match="tei:term" mode="toc"> </xsl:template>
  <xsl:template match="tei:hi" mode="toc">
    <xsl:apply-templates/>
  </xsl:template>
  <!--   TOC FOR FRONT AND BACK TOO?     -->
  <xsl:template match="tei:front/tei:head" mode="toc">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="tei:back/tei:head" mode="toc">
    <xsl:apply-templates/>
  </xsl:template>
  <!--   SUBMENU EXTRAS     -->
  <xsl:template match="tei:head" mode="submenu">
    <xsl:apply-templates mode="submenu"/>
  </xsl:template>
  <xsl:template match="tei:note" mode="submenu"> </xsl:template>
  <xsl:template match="tei:hi" mode="submenu">
    <xsl:apply-templates/>
  </xsl:template>
  <!--   BLOCK LEVEL     -->
  <!-- Creates anchor if there is @xml:id -->
  <xsl:template name="a-id">
    <xsl:if test="@xml:id">
      <xsl:attribute name="id">
        <xsl:value-of select="@xml:id"/>
      </xsl:attribute>
    </xsl:if>
  </xsl:template>
  <!--   PARAS     -->

  <xsl:template name="p-num">
    <p class="center"><xsl:value-of select="concat('[',count(preceding-sibling::tei:p) +1,']')"/></p>
   </xsl:template>


  <xsl:template match="tei:p">
    <xsl:if test="not(ancestor::tei:list[@type='gallery-list']) and not(ancestor::tei:figure)">
            <xsl:call-template name="p-num" />
     </xsl:if>
      <p>
          <xsl:call-template name="a-id"/>

          <xsl:apply-templates/>
        </p>

  </xsl:template>
  <!--   LISTS     -->

  <xsl:template name="list-head">
    <xsl:if test="tei:head">
      <h3>
        <xsl:apply-templates select="tei:head"/>
      </h3>
    </xsl:if>
  </xsl:template>

  <xsl:template name="list-models">
    <!-- Basic list formatting starts -->

        <xsl:call-template name="list-head"/>
        <ul>
          <xsl:call-template name="a-id"/>
          <xsl:apply-templates select="*[not(local-name()='head')]"/>
        </ul>

    <!-- Basic list formatting ends -->
  </xsl:template>
  <xsl:template match="tei:list">
    <xsl:choose>

      <!-- CASE: Full sized images in a list -->
      <xsl:when test="@type='gallery-list'">
        <div id="gallery" class="content" style="display: block">
          <div id="controls" class="controls"><xsl:text> </xsl:text></div>
          <div id="caption" class="embox"><xsl:text> </xsl:text></div>
          <div id="loading" class="loader"><xsl:text> </xsl:text></div>
          <div id="slideshow" class="slideshow"><xsl:text> </xsl:text></div>
        </div>


        <div id="thumbs">
          <ul class="thumbs noscript">
          <xsl:apply-templates/>
          </ul>

        </div>
      </xsl:when>
      <xsl:when test="@type='gloss'">
        <dl>
          <xsl:call-template name="a-id"/>
          <xsl:apply-templates/>
        </dl>
      </xsl:when>
      <xsl:when test="@type='special'">
        <xsl:if test="tei:head">
          <h2>
            <xsl:apply-templates select="tei:head"/>
          </h2>
        </xsl:if>
        <div >
          <div >
            <dl>
              <xsl:call-template name="a-id"/>
              <xsl:apply-templates select="tei:item"/>
            </dl>
          </div>
        </div>
      </xsl:when>

    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:item">
    <xsl:choose>
      <!-- Figure in lists -->
      <!-- CASE 1: Full sized figures in a grid -->
      <xsl:when test="../@type='figure-full'">
        <!--<xsl:apply-templates/>-->
      </xsl:when>
      <!-- CASE 2: Thumbnail figures in a grid -->
      <xsl:when test="../@type='figure-thumb'">
        <xsl:apply-templates/>
      </xsl:when>
      <!-- CASE: Full sized images in a list -->
      <xsl:when test="../@type='gallery-list'">
        <li>
          <xsl:apply-templates select="tei:figure/tei:graphic" mode="ojs-gallery"/>
          <div class="caption">

            <div class="download">
              <a href="/jms/public/journals/1/{tei:figure/tei:graphic/@xml:id}_orig.jpg" title="After viewing the original image, press the browser back button to return to this gallery.">View Original Image</a>
            </div>

            <div class="image-title">Fig. <xsl:value-of select="tei:figure/@n"/></div>
            <div class="image-desc">
         <xsl:if test="tei:figure/tei:head">
           <xsl:apply-templates select="tei:figure/tei:head" mode="ojs-gallery"/>
         </xsl:if>
        <xsl:if test="tei:figure/tei:p">
            <xsl:apply-templates select="tei:figure/tei:p"/>

        </xsl:if>
            </div>
        </div>
        </li>
      </xsl:when>
      <!--  CASE 2: Glossary items -->
      <xsl:when test="../@type='gloss'">
        <!-- item HERE -->
        <dt>

          <xsl:apply-templates mode="glossary" select="preceding-sibling::tei:label[1]"/>
        </dt>
        <!-- label HERE -->
        <dd>

          <xsl:apply-templates/>
        </dd>
      </xsl:when>
      <xsl:when test="../@type='special'">
        <dt>

          <xsl:apply-templates mode="glossary" select="preceding-sibling::tei:label[1]"/>
        </dt>
        <xsl:for-each select="tei:label/following-sibling::*">
          <dd>

            <xsl:apply-templates select="."/>
          </dd>
        </xsl:for-each>
      </xsl:when>
      <!--  CASE 3: Items with their own numbers -->
      <xsl:when test="@n">
        <li>
          <xsl:apply-templates select="@n"/>
          <xsl:text>. </xsl:text>
          <xsl:apply-templates/>
        </li>
      </xsl:when>
      <!--  CASE 4: All other list items -->
      <xsl:otherwise>
        <li>
          <xsl:apply-templates/>
        </li>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="tei:head" mode="ojs-gallery">
   <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="tei:graphic" mode="ojs-gallery">
    <xsl:variable name="thisGraphicCaption">
      <xsl:value-of select="normalize-space(concat('Fig. ',../../tei:figure/@n,' ', ../tei:head))"/>
    </xsl:variable>

    <a class="thumb" href="/jms/public/journals/1/{@xml:id}_full.jpg" title="{normalize-space(../tei:head)}">
    <img src="/jms/public/journals/1/{../tei:graphic/@xml:id}_thumb.jpg" alt="{$thisGraphicCaption}" />
   </a>

  </xsl:template>
  <xsl:template match="tei:label" mode="glossary">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="tei:label">
    <strong>
      <xsl:apply-templates/>
    </strong>
    <xsl:text>: </xsl:text>
  </xsl:template>


  <!-- LINE Group -->

  <xsl:template match="tei:lg">
    <blockquote>
      <xsl:attribute name="class">
        <xsl:choose>
          <xsl:when test="@rend='right'">
            <xsl:text>lg right</xsl:text>
          </xsl:when>
          <xsl:when test="@rend='center'">
            <xsl:text>lg center</xsl:text>
          </xsl:when>
          <xsl:when test="starts-with(@rend,'indent(')">
            <xsl:text>indent</xsl:text>
            <xsl:value-of
              select="concat(substring-before(substring-after(@rend,'('),')'),'em')"
            />
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>lg left</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      <xsl:apply-templates/>
    </blockquote>
  </xsl:template>

  <xsl:template match="tei:lg/tei:l">
    <span>
      <xsl:if test="@rend">
      <xsl:attribute name="class">
        <xsl:choose>
          <xsl:when test="@rend='right'">
            <xsl:text>right</xsl:text>
          </xsl:when>
          <xsl:when test="@rend='center'">
            <xsl:text>center</xsl:text>
          </xsl:when>
          <xsl:when test="@rend='left'">
            <xsl:text>left</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>left</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:attribute>
      </xsl:if>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!--   TABLE    -->
  <xsl:template match="tei:table">

        <xsl:call-template name="table-simpleDisplay"/>

  </xsl:template>
  <!--   ROW   -->
  <xsl:template match="tei:row">
    <!-- Parameters passed through -->
    <xsl:param name="number-of-rows"/>
    <xsl:param name="number-of-cells"/>

        <xsl:call-template name="row-simpleDisplay"> </xsl:call-template>

  </xsl:template>
  <!--   CELL   -->
  <xsl:template match="tei:cell">
    <!-- Parameters passed through -->
    <xsl:param name="number-of-rows"/>
    <xsl:param name="number-of-cells"/>
    <xsl:param name="context-row"/>
    <xsl:call-template name="cell-simpleDisplay"/>
    </xsl:template>
  <!-- TEMPLATES FOR SHADING AND ROW NUMBERS -->
  <!-- Template for alternate shading -->
  <xsl:template name="odd-even">
    <xsl:choose>
      <xsl:when test="../@type='gloss'">
        <xsl:choose>
          <xsl:when test="count(preceding-sibling::tei:item) mod 2 = 0"> z01</xsl:when>
          <xsl:otherwise>
            <xsl:text> z02</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:when test="../@type='special'">
        <xsl:choose>
          <xsl:when test="count(parent::tei:item/preceding-sibling::*) mod 2 = 0"> z01</xsl:when>
          <xsl:otherwise>
            <xsl:text> z02</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <xsl:choose>
          <xsl:when test="count(preceding-sibling::tei:row) mod 2 = 0"> z01</xsl:when>
          <xsl:otherwise>
            <xsl:text> z02</xsl:text>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <!-- Template for counting rows -->
  <xsl:template name="r-num">
    <xsl:choose>
      <xsl:when test="../@type='gloss' or ../@type='special'">
        <xsl:variable name="count-item">
          <xsl:number count="tei:item" format="01" level="single"/>
        </xsl:variable>
        <xsl:text>r</xsl:text>
        <xsl:value-of select="$count-item"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:choose>
          <xsl:when test="not(following-sibling::tei:row)">
            <xsl:text>x02</xsl:text>
          </xsl:when>
          <xsl:otherwise>
            <xsl:text>r</xsl:text>
            <xsl:number count="tei:row" format="01" level="single"/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <!-- Template for counting cells -->
  <xsl:template name="c-num">
    <xsl:choose>
      <xsl:when test="not(following-sibling::tei:cell)">
        <xsl:text>x01</xsl:text>
      </xsl:when>

      <xsl:otherwise>
        <xsl:text>c</xsl:text>
        <xsl:number count="tei:cell" format="01" level="single"/>
      </xsl:otherwise>

    </xsl:choose>
  </xsl:template>
  <!-- Template for Table heads and captions -->
  <xsl:template name="tableHead">
    <xsl:attribute name="title">
      <xsl:value-of select="tei:head"/>
    </xsl:attribute>
    <caption>
      <xsl:value-of select="tei:head"/>
    </caption>
  </xsl:template>
  <xsl:template name="thScope">
    <xsl:attribute name="scope">
      <xsl:choose>
        <xsl:when test="../@role='label'">
          <xsl:text>col</xsl:text>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>row</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:attribute>
  </xsl:template>

  <!-- Test to prevent endless looping -->
  <xsl:template name="consistency-test">
    <xsl:param name="number-of-cells"/>
    <xsl:for-each select="tei:row[position()>1]">
      <xsl:variable name="cur-cell-count" select="count(tei:cell) + sum(tei:cell/@cols) -
        count(tei:cell/@cols)"/>
      <xsl:if test="$cur-cell-count > $number-of-cells">
        <xsl:text>1</xsl:text>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>
  <xsl:template name="table-complexDisplay">
    <!-- Number of rows in the table. -->
    <xsl:variable name="number-of-rows" select="count(tei:row)"/>
    <!-- Number of columns in a row. -->
    <xsl:variable name="number-of-cells" select="count(tei:row[position() = 1]/tei:cell) +
      sum(tei:row[position() = 1]/tei:cell/@cols) - count(tei:row[position() = 1]/tei:cell/@cols)"/>
    <!-- To prevent extra cells causing the process to break -->
    <xsl:variable name="error">
      <xsl:call-template name="consistency-test">
        <xsl:with-param name="number-of-cells" select="$number-of-cells"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:choose>
      <!-- Test to prevent endless looping -->
      <xsl:when test="contains($error, '1')">
        <h3>Error converting table. Please check encoding for extra cells or missing colspans.</h3>
      </xsl:when>
      <!-- Output -->
      <xsl:otherwise>
        <div>
          <xsl:call-template name="a-id"/>
          <div>
            <table class="article-table unstriped">
              <xsl:if test="string(tei:head)">
                <xsl:call-template name="tableHead"/>
              </xsl:if>
              <xsl:if test="tei:row[@role='label']">
                <thead>
                  <xsl:apply-templates select="tei:row[@role='label']">
                    <xsl:with-param name="number-of-rows" select="$number-of-rows"/>
                    <xsl:with-param name="number-of-cells" select="$number-of-cells"/>
                  </xsl:apply-templates>
                </thead>
              </xsl:if>
              <tbody>
                <xsl:apply-templates select="tei:row[not(@role='label')]">
                  <xsl:with-param name="number-of-rows" select="$number-of-rows"/>
                  <xsl:with-param name="number-of-cells" select="$number-of-cells"/>
                </xsl:apply-templates>
              </tbody>
            </table>
          </div>
        </div>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template name="row-complexDisplay">
    <!-- Parameters passed through -->
    <xsl:param name="number-of-rows"/>
    <xsl:param name="number-of-cells"/>

    <tr>

      <xsl:apply-templates>
        <xsl:with-param name="number-of-rows" select="$number-of-rows"/>
        <xsl:with-param name="number-of-cells" select="$number-of-cells"/>
        <xsl:with-param name="context-row" select="count(preceding-sibling::tei:row) + 1"/>
      </xsl:apply-templates>
    </tr>
  </xsl:template>
  <xsl:template name="cell-complexDisplay">
    <!-- Parameters passed through -->
    <xsl:param name="number-of-rows"/>
    <xsl:param name="number-of-cells"/>
    <xsl:param name="context-row"/>
    <xsl:choose>
      <!-- Heading cells -->
      <xsl:when test="@role='label'">
        <th>
          <xsl:call-template name="cell-att">
            <xsl:with-param name="number-of-rows" select="$number-of-rows"/>
            <xsl:with-param name="number-of-cells" select="$number-of-cells"/>
            <xsl:with-param name="context-row" select="$context-row"/>
          </xsl:call-template>
          <xsl:apply-templates/>
        </th>
      </xsl:when>
      <!-- Data cells -->
      <xsl:otherwise>
        <td>
          <xsl:call-template name="cell-att">
            <xsl:with-param name="number-of-rows" select="$number-of-rows"/>
            <xsl:with-param name="number-of-cells" select="$number-of-cells"/>
            <xsl:with-param name="context-row" select="$context-row"/>
          </xsl:call-template>
          <xsl:apply-templates/>
        </td>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <!--  TABLE: simpleDisplay model  -->
  <xsl:template name="table-simpleDisplay">
    <div >
      <xsl:call-template name="a-id"/>
      <!-- Type only changes if a project needs different formatting-->
      <div>
        <table class="article-table unstriped">
          <xsl:if test="string(tei:head)">
            <xsl:call-template name="tableHead"/>
          </xsl:if>
          <xsl:if test="tei:row[@role='label']">
            <thead>
              <xsl:apply-templates select="tei:row[@role='label']"/>
            </thead>
          </xsl:if>
          <tbody>
            <xsl:apply-templates select="tei:row[@role='data' or not(@role)]"/>
          </tbody>
        </table>
      </div>
    </div>
  </xsl:template>
  <xsl:template name="row-simpleDisplay">
    <!-- Variable for alternate shading -->
    <xsl:variable name="oddeven">
      <xsl:call-template name="odd-even"/>
    </xsl:variable>
    <!-- Variable for counting rows -->
    <xsl:variable name="r-num">
      <xsl:call-template name="r-num"/>
    </xsl:variable>
    <tr>

      <xsl:apply-templates/>
    </tr>
  </xsl:template>
  <xsl:template name="cell-simpleDisplay">
    <!-- Variable for counting cells -->
    <xsl:variable name="c-num">
      <xsl:call-template name="c-num"/>
    </xsl:variable>
    <xsl:choose>
      <!-- Heading cells -->
      <xsl:when test="@role='label'">
        <th>

          <xsl:call-template name="thScope"/>
          <xsl:apply-templates/>
        </th>
      </xsl:when>
      <!-- Data cells -->
      <xsl:otherwise>
        <td>

          <xsl:apply-templates/>
        </td>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <!-- COMPLEX TABLE: complexDisplay cell attribute template -->
  <xsl:template name="cell-att">
    <xsl:param name="number-of-rows"/>
    <xsl:param name="number-of-cells"/>
    <xsl:param name="context-row"/>
    <!-- Context cell position -->
    <xsl:variable name="con-cell-position" select="count(preceding-sibling::tei:cell)  +
      sum(preceding-sibling::tei:cell/@cols) - count(preceding-sibling::tei:cell/@cols) + 1"/>
    <xsl:variable name="updated-position">
      <xsl:call-template name="update-position">
        <xsl:with-param name="number-of-rows" select="$number-of-rows"/>
        <xsl:with-param name="number-of-cells" select="$number-of-cells"/>
        <xsl:with-param name="context-row" select="$context-row"/>
        <xsl:with-param name="con-cell" select="$con-cell-position"/>
        <!-- Cell position -->
        <xsl:with-param name="cell" select="1"/>
        <!-- Row position -->
        <xsl:with-param name="row" select="1"/>
        <!-- Total number of cells in the table -->
        <xsl:with-param name="count" select="count(ancestor::tei:table//tei:cell)"/>
        <xsl:with-param name="pos" select="$con-cell-position"/>
      </xsl:call-template>
    </xsl:variable>
    <!-- Output value of the column position -->
    <xsl:variable name="col-position">
      <xsl:choose>
        <!-- Test for last cell -->
        <!-- No spanning cell -->
        <xsl:when test="$updated-position = $number-of-cells">
          <xsl:text>x01</xsl:text>
        </xsl:when>
        <!-- Colspan on self -->
        <xsl:when test="$updated-position +@cols - 1 = $number-of-cells">
          <xsl:text>x01</xsl:text>
        </xsl:when>
        <!-- Normal numbering -->
        <xsl:otherwise>
          <xsl:text>c</xsl:text>
          <xsl:number format="01" value="$updated-position"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <!-- rowspan and colspan attributes -->
    <xsl:if test="string(@rows) and not(@rows='1')">
      <xsl:attribute name="rowspan">
        <xsl:value-of select="@rows"/>
      </xsl:attribute>
    </xsl:if>
    <xsl:if test="string(@cols) and not(@cols='1')">
      <xsl:attribute name="colspan">
        <xsl:value-of select="@cols"/>
      </xsl:attribute>
    </xsl:if>
  </xsl:template>
  <!--
        Recursive template to calculate the position of cells in the table according to the previous cells.
        The new position of the cell depends on the rowspans and colspans of the sibling cells and the cells in the
        previous rows.
    -->
  <xsl:template name="update-position">
    <xsl:param name="number-of-rows"/>
    <xsl:param name="number-of-cells"/>
    <xsl:param name="context-row"/>
    <xsl:param name="con-cell"/>
    <xsl:param name="cell"/>
    <xsl:param name="row"/>
    <xsl:param name="count"/>
    <xsl:param name="pos"/>
    <xsl:choose>
      <!-- Stop condition -->
      <xsl:when test="$count > 0">
        <!-- Update the count -->
        <xsl:variable name="new-count">
          <xsl:choose>
            <xsl:when test="ancestor::tei:table/tei:row[position() = $row]/tei:cell[position() =
              $cell]">
              <xsl:value-of select="$count - 1"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$count"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <xsl:variable name="new-pos">
          <xsl:choose>
            <xsl:when test="ancestor::tei:table/tei:row[position() = $row and $context-row >
              position()]/tei:cell[position() = $cell and @rows]">
              <!-- Cases where preceding-siblings of the cell being tested have colspan -->
              <xsl:variable name="pre-cols" select="sum(ancestor::tei:table/tei:row[position() =
                $row]/tei:cell[position() = $cell]/preceding-sibling::tei:cell[$cell >
                position()]/@cols)"/>
              <!--
                The position of the context cell is updated if there are rowspans in previous cells of the previous rows and the
                column spans until the context cell position.
              -->
              <xsl:choose>
                <xsl:when test="$pos >= $cell + $pre-cols and $row +
                  ancestor::tei:table/tei:row[position() = $row]/tei:cell[position() = $cell]/@rows
                  - 1 >= $context-row">
                  <!--
                    Creates the value that is added to the context cell position. Where there are colspans, it adds the value of the colspan,
                    otherwise it just increases the value of the context cell by one.
                  -->
                  <xsl:variable name="step">
                    <xsl:choose>
                      <xsl:when test="ancestor::tei:table/tei:row[position() =
                        $row]/tei:cell[position() = $cell and @cols]">
                        <xsl:value-of select="ancestor::tei:table/tei:row[position() =
                          $row]/tei:cell[position() = $cell]/@cols"/>
                      </xsl:when>
                      <xsl:otherwise>1</xsl:otherwise>
                    </xsl:choose>
                  </xsl:variable>
                  <xsl:value-of select="$pos + $step"/>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:value-of select="$pos"/>
                </xsl:otherwise>
              </xsl:choose>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$pos"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <!-- Position of the new cell being tested -->
        <xsl:variable name="new-cell">
          <xsl:choose>
            <xsl:when test="$number-of-cells > $cell">
              <xsl:value-of select="$cell + 1"/>
            </xsl:when>
            <xsl:otherwise>1</xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <!-- Checks if the row position needs to be incremented -->
        <xsl:variable name="new-row">
          <xsl:choose>
            <xsl:when test="$cell = $number-of-cells">
              <xsl:value-of select="$row + 1"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="$row"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        <!--
          Recurs a call to the current template with the updated values of the context cell position, previous row position and previous cell
          position that was tested last.
        -->
        <xsl:call-template name="update-position">
          <xsl:with-param name="number-of-rows" select="$number-of-rows"/>
          <xsl:with-param name="number-of-cells" select="$number-of-cells"/>
          <xsl:with-param name="context-row" select="$context-row"/>
          <xsl:with-param name="con-cell" select="$con-cell"/>
          <xsl:with-param name="cell" select="$new-cell"/>
          <xsl:with-param name="row" select="$new-row"/>
          <xsl:with-param name="count" select="$new-count"/>
          <xsl:with-param name="pos" select="$new-pos"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$pos"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <!--  END Table templates     -->
  <!--   NEW BIB SECTION     -->
  <xsl:template match="tei:listBibl">
    <ul>
      <xsl:apply-templates/>
    </ul>
  </xsl:template>
  <xsl:template match="tei:bibl[parent::tei:listBibl]">
    <li>
      <xsl:apply-templates/>
    </li>
  </xsl:template>
  <xsl:template match="tei:listBibl/tei:head">
    <caption>
      <strong>
        <xsl:apply-templates/>
      </strong>
    </caption>
  </xsl:template>
  <xsl:template match="tei:title">
    <em>
      <xsl:apply-templates/>
    </em>
  </xsl:template>
  <xsl:template match="tei:author">

      <xsl:apply-templates/>

  </xsl:template>
  <!--   BLOCKQUOTES   -->
  <xsl:template match="tei:q">
    <blockquote><p>
      <xsl:apply-templates/>
      </p>
    </blockquote>
  </xsl:template>
  <!--   ADDRESSES   -->
  <xsl:template match="tei:address">
    <address>
      <xsl:apply-templates/>
    </address>
    <xsl:if test="following-sibling::tei:address">
      <br/>
    </xsl:if>
  </xsl:template>
  <xsl:template match="tei:addrLine">
    <!-- START automatic links or email addresses -->
    <xsl:choose>
      <xsl:when test="tei:email">
        <a href="mailto:{tei:email}">
          <xsl:apply-templates/>
        </a>
      </xsl:when>
      <xsl:when test="tei:ref">
        <a href="{tei:ref/@target}">
          <xsl:apply-templates/>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
    <!-- END automatic links or email addresses -->
    <xsl:if test="following-sibling::tei:addrLine">
      <br/>
    </xsl:if>
  </xsl:template>
  <!--   FIGURES   -->
  <!-- NINETEEN: Figures are suppressed at the point of occurrence, and specifically processed after the body of the text -->
    <xsl:template match="tei:graphic"/>
    <xsl:template match="tei:figDesc"/>
    <xsl:template match="tei:figure/tei:head"/>

  <!-- NINETEEN: Figures are suppressed at the point of occurrence, and specifically processed after the body of the text -->
  <xsl:template match="tei:figure"/>


  <!--   PHRASE LEVEL   -->
  <!--   LINKS: xref   -->
  <xsl:template match="tei:ref">
    <xsl:choose>
      <xsl:when test="@type  = 'external' or @rend = 'external'">
        <a href="{@target}">
          <xsl:call-template name="external-link"/>
          <xsl:apply-templates/>
        </a>
      </xsl:when>

    </xsl:choose>
  </xsl:template>
  <xsl:template name="external-link">
    <xsl:choose>
      <!-- Open in a new window -->
      <xsl:when test="@rend='newWindow'">

        <xsl:attribute name="rel">
          <xsl:text>external</xsl:text>
        </xsl:attribute>
        <xsl:attribute name="title">
          <xsl:text>External website (Opens in a new window)</xsl:text>
        </xsl:attribute>
      </xsl:when>
      <!-- Open in same window -->
      <xsl:otherwise>

        <xsl:attribute name="title">
          <xsl:text>External website</xsl:text>
        </xsl:attribute>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template name="internal-link">
    <xsl:param name="title"/>
    <xsl:choose>
      <!-- Open in a new window -->
      <xsl:when test="@rend='newWindow'">

        <xsl:attribute name="rel">
          <xsl:text>external</xsl:text>
        </xsl:attribute>
        <xsl:attribute name="title">
          <xsl:text>Link to </xsl:text>
          <xsl:value-of select="$title"/>
          <xsl:text> (Opens in a new window)</xsl:text>
        </xsl:attribute>
      </xsl:when>
      <!-- Open in same window -->
      <xsl:otherwise>

        <xsl:attribute name="title">
          <xsl:text>Link to </xsl:text>
          <xsl:value-of select="$title"/>
        </xsl:attribute>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template match="tei:email">
    <a href="mailto:" title="Email link">
      <xsl:apply-templates/>
    </a>
  </xsl:template>

  <xsl:template match="tei:anchor">
    <a id="{@xml:id}"/>
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="tei:ptr">
    <a href="{@target}">
      <xsl:choose>
        <xsl:when test="starts-with(@target, 'http://')">
          <xsl:call-template name="external-link"/>
        </xsl:when>
        <xsl:when test="starts-with(@target, '#')">
          <a href="{@target}" title="Link internal to this page">
            <xsl:apply-templates/>
          </a>
        </xsl:when>
        <xsl:otherwise>
          <xsl:attribute name="title">
            <xsl:text>Encoding error: @traget does not start with 'http://' and not internal link</xsl:text>
          </xsl:attribute>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:apply-templates select="@target"/>
    </a>
  </xsl:template>
  <!--  UBI     -->
  <xsl:template match="tei:hi">
    <xsl:choose>
      <!-- ITALICS -->
      <xsl:when test="@rend='italic'">
        <em>
          <xsl:apply-templates/>
        </em>
      </xsl:when>
      <!-- BOLD -->
      <xsl:when test="@rend='bold'">
        <strong>
          <xsl:apply-templates/>
        </strong>
      </xsl:when>
      <!-- BOLD AND ITALICS -->
      <xsl:when test="@rend='bolditalic'">
        <strong>
          <em>
            <xsl:apply-templates/>
          </em>
        </strong>
      </xsl:when>
      <xsl:when test="@rend='sup'">
        <sup>
          <xsl:apply-templates/>
        </sup>
      </xsl:when>
      <xsl:when test="@rend='sub'">
        <sub>
          <xsl:apply-templates/>
        </sub>
      </xsl:when>
      <!-- CURRENT DEFAULT: italics -->
      <xsl:otherwise>
        <em>
          <xsl:apply-templates/>
        </em>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <!--   FOOTNOTES     -->
  <xsl:template match="tei:note">
    <sup>
      <a >
        <xsl:attribute name="href">
          <xsl:text>#fn</xsl:text>
          <xsl:number format="01" from="tei:text" level="any"/>
        </xsl:attribute>
        <xsl:attribute name="id">
          <xsl:text>fnLink</xsl:text>
          <xsl:number format="01" from="tei:text" level="any"/>
        </xsl:attribute>
        <xsl:number from="tei:text" level="any"/>
      </a>
    </sup>
    <!--  TOOK OUT THIS: count="note" from="group/text" -->
  </xsl:template>

  <xsl:template name="ctpl_footnotes">
    <xsl:if test="//tei:note">
      <div >
        <h3>Endnotes</h3>
        <ol>
          <!-- START model for each footnote -->
          <xsl:for-each select="//tei:note">
            <!-- Variables -->
            <xsl:variable name="fnnum">
              <xsl:number level="any"/>
            </xsl:variable>
            <xsl:variable name="fnnumfull">
              <xsl:number level="any" format="01"/>
            </xsl:variable>
            <!-- Output -->
            <li id="fn{$fnnumfull}">
                <xsl:apply-templates/><xsl:text> [</xsl:text>
              <a href="#fnLink{$fnnumfull}" >^</a><xsl:text>]</xsl:text>
            </li>
          </xsl:for-each>
          <!-- END model for each footnote -->
        </ol>
      </div>
    </xsl:if>
  </xsl:template>



  <xsl:template name="ctpl_figure">
    <xsl:if test="//tei:figure and not(//tei:list[@type='gallery-list'])">
      <div >
        <h3>Figures</h3>
        <dl>
          <!-- START model for each footnote -->
          <xsl:for-each select="//tei:figure">

             <dd>
               <img src="/jms/public/journals/1/{tei:graphic/@xml:id}_full.jpg"/>
               <p>
                 <em>Fig. <xsl:value-of select="@n"/></em><xsl:text> </xsl:text><xsl:apply-templates select="tei:head" mode="ojs-gallery"/>
               </p>
               <xsl:apply-templates select="tei:p"/>
             </dd>
          </xsl:for-each>
          <!-- END model for each footnote -->
        </dl>
      </div>
    </xsl:if>
  </xsl:template>


  <!--   VARIOUS TERMS   -->
  <xsl:template match="tei:foreign">
    <em>
      <xsl:apply-templates/>
    </em>
  </xsl:template>
  <xsl:template match="tei:rs">
    <strong>
      <xsl:apply-templates/>
    </strong>
  </xsl:template>
  <xsl:template match="tei:date[not(ancestor::tei:bibl)]">
    <strong>
      <xsl:apply-templates/>
    </strong>
  </xsl:template>
  <xsl:template match="tei:emph">
    <em>
      <xsl:apply-templates/>
    </em>
  </xsl:template>
  <xsl:template match="tei:del">
    <del>
      <xsl:apply-templates/>
    </del>
  </xsl:template>
  <xsl:template match="tei:code">
    <pre>
    <xsl:apply-templates/>
  </pre>
  </xsl:template>
  <xsl:template match="tei:lb">
    <br/>
  </xsl:template>

  <xsl:template match="tei:ab">
    <xsl:choose>
      <xsl:when test="@type='form'">
        <form method="post" name="{@xml:id}">
          <xsl:attribute name="action">
            <!--  probably:  http://curlew.cch.kcl.ac.uk/cgi-bin/doemail.pl-->
          </xsl:attribute>
          <input name="script" type="hidden" value="crsbi_fb"/>
          <p >
            <xsl:for-each select="tei:seg[@type='input']">
              <xsl:value-of select="preceding-sibling::tei:label[1]"/>
              <xsl:text>:</xsl:text>
              <br/>
              <input style="background-color: rgb(255, 255, 160);" type="text">
                <xsl:choose>
                  <xsl:when test="contains(preceding-sibling::tei:label[1],'(')">
                    <xsl:attribute name="id">
                      <xsl:value-of select="substring-before(preceding-sibling::tei:label[1], '(')"
                      />
                    </xsl:attribute>
                  </xsl:when>
                  <xsl:when test="contains(preceding-sibling::tei:label[1],':')">
                    <xsl:attribute name="id">
                      <xsl:value-of select="substring-before(preceding-sibling::tei:label[1], ':')"
                      />
                    </xsl:attribute>
                  </xsl:when>
                  <xsl:otherwise>
                    <xsl:value-of select="preceding-sibling::tei:label[1]"/>
                  </xsl:otherwise>
                </xsl:choose>
              </input>
              <br/>
            </xsl:for-each>
          </p>
          <xsl:if test="tei:seg[@type='textfield']">
            <xsl:for-each select="tei:seg[@type='textfield']">
              <p >
                <xsl:value-of select="preceding-sibling::tei:label[1]"/>
                <xsl:text>:</xsl:text>
              </p>
              <p >
                <textarea cols="40" rows="6">
                  <xsl:choose>
                    <xsl:when test="contains(preceding-sibling::tei:label[1],'(')">
                      <xsl:attribute name="id">
                        <xsl:value-of select="substring-before(preceding-sibling::tei:label[1],
                          '(')"/>
                      </xsl:attribute>
                    </xsl:when>
                    <xsl:when test="contains(preceding-sibling::tei:label[1],':')">
                      <xsl:attribute name="id">
                        <xsl:value-of select="substring-before(preceding-sibling::tei:label[1],
                          ':')"/>
                      </xsl:attribute>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:value-of select="preceding-sibling::tei:label[1]"/>
                    </xsl:otherwise>
                  </xsl:choose> &#x00A0; </textarea>
              </p>
            </xsl:for-each>
          </xsl:if>
          <xsl:if test="tei:list[@type='select']">
            <p >
              <label for="fe01">
                <xsl:value-of select="tei:list[@type='select']/preceding-sibling::tei:label[1]"/>
                <xsl:text>: </xsl:text>
              </label>
              <select id="fe01" name="fe01">
                <option selected="selected"> Please select... </option>
                <xsl:for-each select="tei:list[@type='select']/tei:item">
                  <option value="{.}">
                    <xsl:text> </xsl:text>
                    <xsl:value-of select="."/>
                    <xsl:text> </xsl:text>
                  </option>
                </xsl:for-each>
              </select>
            </p>
          </xsl:if>
          <p >
            <input name="Submit" type="submit" value="Submit"/>
            <input name="Reset" type="reset" value="Reset"/>
          </p>
        </form>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <!--   SEARCHABLE TESTS   -->
  <xsl:template match="tei:name">
    <span>
      <xsl:attribute name="id">
        <xsl:value-of select="ancestor::tei:TEI/@xml:id"/>
        <xsl:text>-</xsl:text>
        <xsl:number level="any"/>
      </xsl:attribute>
      <xsl:apply-templates/>
    </span>
  </xsl:template>
</xsl:stylesheet>
