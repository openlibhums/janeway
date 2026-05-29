<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:janeway ="https://janeway.systems">
  <xsl:output method="html" indent="yes" encoding="utf-8" omit-xml-declaration="yes"/>
  <xsl:template match="/sitemap:sitemapindex|/sitemap:urlset" >
    <xsl:variable name="page_title">
      <xsl:choose>
        <xsl:when test="janeway:page_title">
          <xsl:value-of select="janeway:page_title"/>
        </xsl:when>
        <xsl:otherwise>Sitemap - <xsl:value-of select="janeway:sitemap_name"/></xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="h1_text">
      <xsl:choose>
        <xsl:when test="janeway:h1">
          <xsl:value-of select="janeway:h1"/>
        </xsl:when>
        <xsl:otherwise>Sitemap - <xsl:value-of select="janeway:sitemap_name"/></xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <html lang="en" xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <title><xsl:value-of select="$page_title"/></title>
        <meta http-equiv="content-type" content="text/html; charset=utf-8" />
        <style type="text/css">
          body {
            font-size: 1rem;
          }
          li[aria-current="true"] {
            font-weight: bold;
          }
          li[aria-current="true"] li {
            font-weight: normal;
          }
        </style>
      </head>
      <body>
        <main>
          <h1><xsl:value-of select="$h1_text"/></h1>
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
          <xsl:if test="//janeway:note">
            <section aria-labelledby="sitemap_note">
              <h2 id="sitemap_note">Note</h2>
              <p><xsl:value-of select="//janeway:note"/></p>
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
              <xsl:choose>
                <xsl:when test="sitemap:sitemap/janeway:group">
                  <!-- Press sitemap: render each group as an H3 section -->
                  <xsl:if test="sitemap:sitemap[janeway:group='pages']">
                    <section aria-labelledby="lower_pages">
                      <h3 id="lower_pages">Pages</h3>
                      <ul>
                        <xsl:for-each select="sitemap:sitemap[janeway:group='pages']">
                          <li>
                            <xsl:variable name="itemURL"><xsl:value-of select="sitemap:loc"/></xsl:variable>
                            <a href="{$itemURL}"><xsl:value-of select="janeway:loc_label"/></a>
                          </li>
                        </xsl:for-each>
                      </ul>
                    </section>
                  </xsl:if>
                  <xsl:if test="sitemap:sitemap[janeway:group='news']">
                    <section aria-labelledby="lower_news">
                      <h3 id="lower_news">News</h3>
                      <ul>
                        <xsl:for-each select="sitemap:sitemap[janeway:group='news']">
                          <li>
                            <xsl:variable name="itemURL"><xsl:value-of select="sitemap:loc"/></xsl:variable>
                            <a href="{$itemURL}"><xsl:value-of select="janeway:loc_label"/></a>
                          </li>
                        </xsl:for-each>
                      </ul>
                    </section>
                  </xsl:if>
                  <xsl:if test="sitemap:sitemap[janeway:group='journals']">
                    <section aria-labelledby="lower_journals">
                      <h3 id="lower_journals">Journals</h3>
                      <ul>
                        <xsl:for-each select="sitemap:sitemap[janeway:group='journals']">
                          <li>
                            <xsl:variable name="itemURL"><xsl:value-of select="sitemap:loc"/></xsl:variable>
                            <a href="{$itemURL}"><xsl:value-of select="janeway:loc_label"/></a>
                          </li>
                        </xsl:for-each>
                      </ul>
                    </section>
                  </xsl:if>
                  <xsl:if test="sitemap:sitemap[janeway:group='repositories']">
                    <section aria-labelledby="lower_repos">
                      <h3 id="lower_repos">Repositories</h3>
                      <ul>
                        <xsl:for-each select="sitemap:sitemap[janeway:group='repositories']">
                          <li>
                            <xsl:variable name="itemURL"><xsl:value-of select="sitemap:loc"/></xsl:variable>
                            <a href="{$itemURL}"><xsl:value-of select="janeway:loc_label"/></a>
                          </li>
                        </xsl:for-each>
                      </ul>
                    </section>
                  </xsl:if>
                  <xsl:if test="sitemap:sitemap[janeway:group='issues']">
                    <section aria-labelledby="lower_issues">
                      <h3 id="lower_issues">Issues</h3>
                      <ul>
                        <xsl:for-each select="sitemap:sitemap[janeway:group='issues']">
                          <li>
                            <xsl:variable name="itemURL"><xsl:value-of select="sitemap:loc"/></xsl:variable>
                            <a href="{$itemURL}"><xsl:value-of select="janeway:loc_label"/></a>
                          </li>
                        </xsl:for-each>
                      </ul>
                    </section>
                  </xsl:if>
                  <xsl:if test="sitemap:sitemap[janeway:group='subjects']">
                    <section aria-labelledby="lower_subjects">
                      <h3 id="lower_subjects">Subjects</h3>
                      <ul>
                        <xsl:for-each select="sitemap:sitemap[janeway:group='subjects']">
                          <li>
                            <xsl:variable name="itemURL"><xsl:value-of select="sitemap:loc"/></xsl:variable>
                            <a href="{$itemURL}"><xsl:value-of select="janeway:loc_label"/></a>
                          </li>
                        </xsl:for-each>
                      </ul>
                    </section>
                  </xsl:if>
                </xsl:when>
                <xsl:otherwise>
                  <!-- Journal / repo sitemaps: flat list -->
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
                </xsl:otherwise>
              </xsl:choose>
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
                <xsl:if test="//janeway:sitemap_level='press'">
                  <xsl:attribute name="aria-current">true</xsl:attribute>
                </xsl:if>
                <div>Press Index<xsl:if test="//janeway:sitemap_level='press'"> (current)</xsl:if></div>
                <ul>
                  <li>
                    <xsl:if test="//janeway:sitemap_level='press-pages'">
                      <xsl:attribute name="aria-current">true</xsl:attribute>
                    </xsl:if>
                    Press pages<xsl:if test="//janeway:sitemap_level='press-pages'"> (current)</xsl:if>
                  </li>
                  <li>
                    <xsl:if test="//janeway:sitemap_level='press-news'">
                      <xsl:attribute name="aria-current">true</xsl:attribute>
                    </xsl:if>
                    Press news<xsl:if test="//janeway:sitemap_level='press-news'"> (current)</xsl:if>
                  </li>
                  <li>
                    <xsl:if test="//janeway:sitemap_level='journal'">
                      <xsl:attribute name="aria-current">true</xsl:attribute>
                    </xsl:if>
                    <div>Journal Index<xsl:if test="//janeway:sitemap_level='journal'"> (current)</xsl:if></div>
                    <ul>
                      <li>
                        <xsl:if test="//janeway:sitemap_level='journal-pages'">
                          <xsl:attribute name="aria-current">true</xsl:attribute>
                        </xsl:if>
                        Journal pages<xsl:if test="//janeway:sitemap_level='journal-pages'"> (current)</xsl:if>
                      </li>
                      <li>
                        <xsl:if test="//janeway:sitemap_level='journal-news'">
                          <xsl:attribute name="aria-current">true</xsl:attribute>
                        </xsl:if>
                        Journal news<xsl:if test="//janeway:sitemap_level='journal-news'"> (current)</xsl:if>
                      </li>
                      <li>
                        <xsl:if test="//janeway:sitemap_level='issue'">
                          <xsl:attribute name="aria-current">true</xsl:attribute>
                        </xsl:if>
                        Issues (one sitemap per issue)<xsl:if test="//janeway:sitemap_level='issue'"> (current)</xsl:if>
                      </li>
                      <li>
                        <xsl:if test="//janeway:sitemap_level='not-in-any-issue'">
                          <xsl:attribute name="aria-current">true</xsl:attribute>
                        </xsl:if>
                        Not in any issue<xsl:if test="//janeway:sitemap_level='not-in-any-issue'"> (current)</xsl:if>
                      </li>
                    </ul>
                  </li>
                  <li>
                    <xsl:if test="//janeway:sitemap_level='repository'">
                      <xsl:attribute name="aria-current">true</xsl:attribute>
                    </xsl:if>
                    <div>Repository Index<xsl:if test="//janeway:sitemap_level='repository'"> (current)</xsl:if></div>
                    <ul>
                      <li>
                        <xsl:if test="//janeway:sitemap_level='repository-pages'">
                          <xsl:attribute name="aria-current">true</xsl:attribute>
                        </xsl:if>
                        Repository pages<xsl:if test="//janeway:sitemap_level='repository-pages'"> (current)</xsl:if>
                      </li>
                      <li>
                        <xsl:if test="//janeway:sitemap_level='subject'">
                          <xsl:attribute name="aria-current">true</xsl:attribute>
                        </xsl:if>
                        Subjects (one sitemap per subject)<xsl:if test="//janeway:sitemap_level='subject'"> (current)</xsl:if>
                      </li>
                      <li>
                        <xsl:if test="//janeway:sitemap_level='not-in-any-subject'">
                          <xsl:attribute name="aria-current">true</xsl:attribute>
                        </xsl:if>
                        Not in any subject<xsl:if test="//janeway:sitemap_level='not-in-any-subject'"> (current)</xsl:if>
                      </li>
                    </ul>
                  </li>
                </ul>
              </li>
            </ul>
            <p>
              Not every level will exist on every Janeway install. Sitemaps are
              only generated for sections that have published content — for
              example, a press with no news items will have no News sitemap, and
              a journal with no published issues will have no Issue sitemaps.
            </p>
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
