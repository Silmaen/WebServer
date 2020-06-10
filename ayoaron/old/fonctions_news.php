<?php



function draw_colone_gauche_news() {?>
	<p>Les News</p>
<?PHP }

function draw_colone_centre_news() {
	echo "					<h1>Les News:</h1>\n";
	require_once("fonctions_bd.php");
	$idcom=connexion_bd();
	$sql = mysqli_query($idcom,"SELECT * FROM news ORDER BY date DESC LIMIT 0,10"); 
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

function draw_colone_droite_news() {?>
	<p>Les News</p>
<?PHP }

?>
