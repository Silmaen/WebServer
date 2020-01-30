<?PHP

function draw_colone_gauche_devel(){
echo "					<h4>les releases<h4>\n";
echo "					<p><table><tr><td><A Href=\"releases/ayoaron_0.0.6.7z \">Version 0.0.6         </A></td></tr><tr><td><A Href=\"docprojet_0.0.6/index.html\">doc version 0.0.6</A></td></tr></table></p>\n";
echo "					<p><table><tr><td><A Href=\"releases/ayoaron_0.0.5.rar\">Version 0.0.5         </A></td></tr><tr><td></td></tr></table></p>\n";
echo "					<p><table><tr><td><A Href=\"releases/ayoaron_0.0.4_20111130.rar\">Version 0.0.4</A></td></tr><tr><td></td></tr></table></p>\n";
}

function draw_colone_droite_devel(){
	if ($_SESSION['acreditation']>5) {
	echo "					<h2>
						Navigation
					</h2>
					<p>
						<A Href=\"docprojet/index.html\" title=\"Documentation de l'API du projet en version html\">API du projet</A>
					</p>
					<p>
						<A Href=\"../mantis\" title=\"Bug tracker et gestion du développement\">avancement du projet</A>
					</p>\n";
	}
}

function draw_colone_centre_devel(){
	echo "					<h1>Articles de développement:</h1>\n";
	require_once("fonctions_bd.php");
	$idcom=connexion_bd();
	$sql = mysqli_query($idcom,"SELECT * FROM develop ORDER BY date DESC LIMIT 0,10"); 
	while ($row = mysqli_fetch_row($sql)) {
		echo "					<article class=\"cadre_news\">
						<div class=\"news_haut\">
							<h1> $row[1] </h1>
						</div>
						<div class=\"news_centre\">
							<p>$row[3]</p> 
						</div>
						<div class=\"news_bas\">
							<adress class=\"news_author\"><em class=\"news_fn\">$row[2]</em></adress> - <time>$row[0]</time>
						</div>
					</article>\n";
	}
	mysqli_close($idcom);
}

?>