<?xml version="1.0"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
	xmlns="http://www.crossref.org/schema/4.4.0" xmlns:xsldoc="http://www.bacman.net/XSLdoc"
	xmlns:xlink="http://www.w3.org/1999/xlink" exclude-result-prefixes="xsldoc">

	<xsl:output method="xml" indent="yes" encoding="UTF-8"/>

	<!-- ========================================================================== -->
	<!-- Root Element                                                               -->
	<!-- ========================================================================== -->
    <xsl:template match="/">
        <output>
            <xsl:apply-templates select="//ref-list"/>
        </output>
    </xsl:template>

	<xsl:template match="ref-list">
		<citation_list>
			<xsl:apply-templates select="ref"/>
		</citation_list>
	</xsl:template>

	<xsl:template match="ref">
		<xsl:variable name="key" select="concat('ref_', @id)"/>
		<citation>
			<xsl:attribute name="key">key<xsl:value-of select="$key"/></xsl:attribute>
			<xsl:apply-templates select="element-citation"/>
			<xsl:apply-templates select="citation"/>
			<xsl:apply-templates select="nlm-citation"/>
			<xsl:apply-templates select="mixed-citation"/>
		</citation>
	</xsl:template>

	<xsl:template match="element-citation | citation | nlm-citation | mixed-citation">
		<xsl:choose>
			<xsl:when test="@publication-type = 'journal' or @citation-type = 'journal'">
				<xsl:if test="issn">
					<issn>
						<xsl:value-of select="//element-citation/issn | //citation/issn |//nlm-citation/issn | //mixed-citation/issn"/>
					</issn>
				</xsl:if>
				<xsl:if test="source">
					<journal_title>
						<xsl:apply-templates select="source"/>
					</journal_title>
				</xsl:if>
                <xsl:if test="pub-id[@pub-id-type='doi']">
                    <doi><xsl:apply-templates select="pub-id[@pub-id-type='doi']"/></doi>
                </xsl:if>
				<xsl:if test="person-group">
					<author><xsl:apply-templates select="person-group/name | person-group/collab"/></author>
				</xsl:if>
				<xsl:if test="volume">
					<volume>
						<xsl:apply-templates select="volume"/>
					</volume>
				</xsl:if>
				<xsl:if test="issue">
					<issue>
						<xsl:apply-templates select="issue"/>
					</issue>
				</xsl:if>
                <xsl:if test="string-name">
                    <author><xsl:apply-templates select="string-name"/></author>
				</xsl:if>
				<xsl:if test="fpage">
					<first_page>
						<xsl:apply-templates select="fpage"/>
					</first_page>
				</xsl:if>
				<xsl:if test="year">
					<xsl:element name="cYear">
						<xsl:value-of select="year"/>
					</xsl:element>
				</xsl:if>
				<xsl:if test="article-title">
					<article_title>
						<xsl:apply-templates select="article-title"/>
					</article_title>
				</xsl:if>
			</xsl:when>
			<xsl:when
				test="@citation-type = 'book' or @citation-type = 'conf-proceedings' or @citation-type = 'confproc' or @citation-type = 'other' or @publication-type = 'book' or @publication-type = 'conf-proceedings' or @publication-type = 'confproc' or @publication-type = 'other'">
				<xsl:if test="source">
					<volume_title>
						<xsl:apply-templates select="source"/>
					</volume_title>
				</xsl:if>
				<xsl:if test="person-group">
					<author><xsl:apply-templates select="person-group/name | person-group/collab"/></author>
				</xsl:if>
                <xsl:if test="string-name">
                    <author><xsl:apply-templates select="string-name"/></author>
				</xsl:if>
				<xsl:if test="edition">
					<edition_number>
						<xsl:apply-templates select="edition"/>
					</edition_number>
				</xsl:if>
				<xsl:if test="fpage">
					<first_page>
						<xsl:apply-templates select="fpage"/>
					</first_page>
				</xsl:if>
				<xsl:if test="year">
					<xsl:element name="cYear">
						<xsl:value-of select="year"/>
					</xsl:element>
				</xsl:if>
				<xsl:if test="article-title">
					<article_title>
						<xsl:apply-templates select="article-title"/>
					</article_title>
				</xsl:if>
			</xsl:when>
			<xsl:otherwise>
				<unstructured_citation>
					<xsl:value-of select="."/>
				</unstructured_citation>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>


</xsl:stylesheet>
