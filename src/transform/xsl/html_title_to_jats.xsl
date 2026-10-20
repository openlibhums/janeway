<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                version="1.0">

    <xsl:output method="xml" encoding="UTF-8" omit-xml-declaration="yes"/>

    <!-- Keep the root wrapper so text-only titles produce a document -->
    <xsl:template match="root">
        <root><xsl:apply-templates/></root>
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

    <!-- text -->
    <xsl:template match="text()">
        <xsl:value-of select="."/>
    </xsl:template>

    <!-- fallback for span and anything else: drop tag, keep content -->
    <xsl:template match="*">
        <xsl:apply-templates/>
    </xsl:template>

</xsl:stylesheet>
