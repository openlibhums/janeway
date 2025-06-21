<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                version="1.0">

    <xsl:output method="xml" indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>

    <!-- Process the root wrapper -->
    <xsl:template match="root">
        <xsl:apply-templates/>
    </xsl:template>

    <!-- <p> -->
    <xsl:template match="p">
        <p><xsl:apply-templates/></p>
    </xsl:template>

    <!-- <li> becomes <p> -->
    <xsl:template match="li">
        <p><xsl:apply-templates/></p>
    </xsl:template>

    <!-- <ul> just applies templates -->
    <xsl:template match="ul">
        <xsl:apply-templates/>
    </xsl:template>

    <!-- <br> -->
    <xsl:template match="br">
        <break/>
    </xsl:template>

    <!-- <strong> / <b> -->
    <xsl:template match="strong | b">
        <bold><xsl:apply-templates/></bold>
    </xsl:template>

    <!-- <em> / <i> -->
    <xsl:template match="em | i">
        <italic><xsl:apply-templates/></italic>
    </xsl:template>

    <!-- <sub> -->
    <xsl:template match="sub">
        <sub><xsl:apply-templates/></sub>
    </xsl:template>

    <!-- <sup> -->
    <xsl:template match="sup">
        <sup><xsl:apply-templates/></sup>
    </xsl:template>

    <!-- <span style="text-decoration: underline;"> -->
    <xsl:template match="span[contains(@style, 'underline')]">
        <underline><xsl:apply-templates/></underline>
    </xsl:template>

    <!-- generic span — just keep content -->
    <xsl:template match="span">
        <xsl:apply-templates/>
    </xsl:template>

    <!-- <s> — drop tag, keep content -->
    <xsl:template match="s">
        <xsl:apply-templates/>
    </xsl:template>

    <!-- mailto -->
    <xsl:template match="a[starts-with(@href, 'mailto:')]">
        <email>
            <xsl:value-of select="substring-after(@href, 'mailto:')"/>
        </email>
    </xsl:template>

    <!-- external link -->
    <xsl:template match="a">
        <ext-link>
            <xsl:attribute name="xlink:href">
                <xsl:value-of select="@href"/>
            </xsl:attribute>
            <xsl:apply-templates/>
        </ext-link>
    </xsl:template>

    <!-- text -->
    <xsl:template match="text()">
        <xsl:value-of select="."/>
    </xsl:template>

    <!-- stray text at root level gets wrapped -->
    <xsl:template match="root/text()[normalize-space()]">
        <p><xsl:value-of select="normalize-space()"/></p>
    </xsl:template>

    <!-- fallback for unhandled tags -->
    <xsl:template match="*">
        <xsl:apply-templates/>
    </xsl:template>

</xsl:stylesheet>
