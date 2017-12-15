<?xml version="1.0" encoding="UTF-8"?>
<!-- ============================================================= -->
<!--  MODULE:    Saxon shell (pipelining) utility stylesheet       -->
<!--  VERSION:   1.0                                               -->
<!--  DATE:      January 2009                                      -->
<!--                                                               -->
<!-- ============================================================= -->

<!-- ============================================================= -->
<!--  SYSTEM:    NCBI Archiving and Interchange Journal Articles   -->
<!--                                                               -->
<!--  PURPOSE:   Provide support for pipelining stylesheets        -->
<!--             directly, using Saxon extensions, in XSLT 2.0     -->
<!--                                                               -->
<!--  PROCESSOR DEPENDENCIES:                                      -->
<!--             Saxon, from Saxonica (www.saxonica.com)           -->
<!--             Tested using Saxon 9.1.0.3 (B and SA)             -->
<!--                                                               -->
<!--  COMPONENTS REQUIRED:                                         -->
<!--             This stylesheet does not stand alone; it is a     -->
<!--             code module for inclusion into another stylesheet -->
<!--             that specifies the steps of the pipeline.         -->
<!--                                                               -->
<!--  INPUT:     Any                                               -->
<!--                                                               -->
<!--  OUTPUT:    Any                                               -->
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

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:saxon="http://saxon.sf.net/"
  version="2.0"
  extension-element-prefixes="saxon">

  <!-- This stylesheet does not stand alone! It is a component
       to be called into XSLT 2.0 shell stylesheets. -->
  
  <xsl:variable name="document" select="/" saxon:assignable="yes"/>
  
  
  <xsl:param name="runtime-params">
    <base-dir>
      <xsl:value-of
        select="replace(base-uri(/), '/[^/]+$','')"/>
    </base-dir>
  </xsl:param>

  <xsl:template match="/">
    <xsl:for-each select="$processes/step/concat('../',.)">
      <saxon:assign name="document"
        select="saxon:transform(
                  saxon:compile-stylesheet(doc(.)),
                  $document,
                  $runtime-params/* )"/>
      <!-- A third argument to saxon:transform could specify
           runtime parameters for any (or all) steps -->
    </xsl:for-each>
    <xsl:sequence select="$document"/>
  </xsl:template>
  
</xsl:stylesheet>
