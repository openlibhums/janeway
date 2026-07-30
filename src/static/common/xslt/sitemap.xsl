<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:janeway ="https://janeway.systems">
  <xsl:output method="html" indent="yes" encoding="utf-8" omit-xml-declaration="yes"/>
  <xsl:template match="/sitemap:sitemapindex|/sitemap:urlset" >
    <html lang="en" xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title>Sitemap - <xsl:value-of select="janeway:sitemap_name"/></title>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <style type="text/css">
          body {
            font-size: 1rem;
          }
        </style>
      </head>
      <body>
        <main>
          <h1>Sitemap - <xsl:value-of select="janeway:sitemap_name"/></h1>
          <xsl:if test="//janeway:higher_sitemap">
            <section aria-labelledby="higher_level">
              <h2 id="higher_level">Higher-level sitemap</h2>
              <ul>
                <li>
                  <xsl:variable name="itemURL">
                    <xsl:value-of select="//janeway:higher_sitemap/janeway:loc"/>
                  </xsl:variable>
                  <a href="{$itemURL}">
                    <xsl:value-of select="//janeway:higher_sitemap/janeway:loc_label"/>
                  </a>
                </li>
              </ul>
            </section>
          </xsl:if>
          <xsl:if test="//sitemap:urlset">
            <section aria-labelledby="this_level">
              <h2 id="this_level">This sitemap</h2>
              <xsl:choose>
                <xsl:when test="//sitemap:urlset/sitemap:url">
                  <ul>
                    <xsl:for-each select="//sitemap:urlset/sitemap:url">
                      <li>
                        <xsl:variable name="itemURL">
                          <xsl:value-of select="sitemap:loc"/>
                        </xsl:variable>
                        <a href="{$itemURL}">
                          <xsl:choose>
                            <xsl:when test="janeway:loc_label">
                              <xsl:value-of select="janeway:loc_label"/>
                            </xsl:when>
                            <xsl:otherwise>
                              <xsl:value-of select="sitemap:loc"/>
                            </xsl:otherwise>
                          </xsl:choose>
                        </a>
                        <xsl:if test="sitemap:lastmod">
                          <span>, </span>
                          <xsl:value-of select="substring(sitemap:lastmod,0,11)"/>
                        </xsl:if>
                      </li>
                    </xsl:for-each>
                  </ul>
                </xsl:when>
                <xsl:otherwise>
                  <p>This sitemap is empty.</p>
                </xsl:otherwise>
              </xsl:choose>
            </section>
          </xsl:if>
          <xsl:if test="sitemap:sitemap/sitemap:loc">
            <section aria-labelledby="lower_level">
              <h2 id="lower_level">Lower-level sitemaps</h2>
              <ul>
                <xsl:for-each select="sitemap:sitemap/sitemap:loc">
                  <li>
                    <xsl:variable name="itemURL">
                      <xsl:value-of select="."/>
                    </xsl:variable>
                    <a href="{$itemURL}">
                      <xsl:value-of select="../janeway:loc_label"/>
                    </a>
                  </li>
                </xsl:for-each>
              </ul>
            </section>
          </xsl:if>
          <section aria-labelledby="about">
            <h2 id="about">About Janeway sitemaps</h2>
            <p>
              This sitemap is designed to be machine-readable. Here we have
              applied a stylesheet to make it more human-friendly. Janeway
              sitemaps operate on the following hierarchy:
            </p>
            <ul>
              <li>
                <div>Press</div>
                <ul>
                  <li>
                    <div>Journal</div>
                    <ul>
                      <li>Issue</li>
                    </ul>
                  </li>
                  <li>
                    <div>Repository</div>
                    <ul>
                      <li>Subject</li>
                    </ul>
                  </li>
                </ul>
              </li>
            </ul>
            <p>
              You can find out more about sitemaps on 
              <a href="https://www.sitemaps.org">sitemaps.org</a>.
            </p>
          </section>
        </main>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
