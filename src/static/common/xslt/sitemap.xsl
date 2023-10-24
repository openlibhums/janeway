<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:html="http://www.w3.org/TR/REC-html40"
                xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
	<xsl:template match="/">
		<html xmlns="http://www.w3.org/1999/xhtml">
			<head>
				<title>XML Sitemap</title>
				<meta http-equiv="content-type" content="text/html; charset=utf-8" />
				<style type="text/css">
					body {
						font-family:"Arial";
						font-size:15px;
					}

					a {
						color:black;
					}

                    th {
                        text-align: left;
                    }
				</style>
			</head>
			<body>
				<h1>Sitemap</h1>
					<p>
						This sitemap is designed to be machine-readable. Here we have applied a stylesheet to make it more human friendly. Janeway sitemaps operate on the following hierarchy:
					</p>
                    <ul>
                        <li>
                            Journal Sitemap Index
                            <ul>
                                <li>
                                    Issue Sitemap Index
                                    <ul>
                                        <li>Issue Sitemap (lists articles)</li>
                                    </ul>
                                </li>
                            </ul>
                        </li>
                        <li>
                            Repository Sitemap Index
                            <ul>
                                <li>
                                    Subject Sitemap Index
                                    <ul>
                                        <li>Subject Sitemap (lists repository objects)</li>
                                    </ul>
                                </li>
                            </ul>
                        </li>
                    </ul>
                    <p>You can find out more about sitemaps on <a href="https://www.sitemaps.org">sitemap.org</a>.</p>
				<div id="content">
                    <xsl:variable name="lower" select="'abcdefghijklmnopqrstuvwxyz'"/>
                    <xsl:variable name="upper" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
					<table>
						<tr style="border-bottom:1px black solid;">
							<th>URL</th>
							<th>Change Frequency</th>
							<th>Last Change</th>
						</tr>
                        <xsl:for-each select="sitemap:sitemapindex/sitemap:sitemap">
							<tr>
								<td>
									<xsl:variable name="itemURL">
										<xsl:value-of select="sitemap:loc"/>
									</xsl:variable>
									<a href="{$itemURL}">
										<xsl:value-of select="sitemap:loc"/>
									</a>
								</td>
								<td>
                                    --
								</td>
								<td>
                                    --
								</td>
							</tr>
						</xsl:for-each>
						<xsl:for-each select="sitemap:urlset/sitemap:url">
							<tr>
								<td>
									<xsl:variable name="itemURL">
										<xsl:value-of select="sitemap:loc"/>
									</xsl:variable>
									<a href="{$itemURL}">
										<xsl:value-of select="sitemap:loc"/>
									</a>
								</td>
								<td>
									<xsl:value-of select="concat(translate(substring(sitemap:changefreq, 1, 1),concat($lower, $upper),concat($upper, $lower)),substring(sitemap:changefreq, 2))"/>
								</td>
								<td>
									<xsl:value-of select="concat(substring(sitemap:lastmod,0,11),concat(' ', substring(sitemap:lastmod,12,5)))"/>
								</td>
							</tr>
						</xsl:for-each>
					</table>
				</div>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>