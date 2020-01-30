<?PHP

require_once("fonctions_bd.php");

function draw_colone_gauche_histoire(){
	echo "					<p>Histoire</p>\n";
	if (($_SESSION['acces']=="oui")&&($_SESSION['login']!="")) {
		$chap=$_POST["typ"];
		$subchap=$_POST["obj"];
		$idcom=connexion_bd();
		$sql = mysqli_query($idcom,"SELECT * FROM Chapitres ORDER BY Numero ASC");
		echo "					<ul id=\"ls_type\">\n";
		while ($row = mysqli_fetch_row($sql)) {
			if ($chap==$row[1])
				echo "						<li><a class=\"ty_actif\" href=\"histoire.php?typ=$row[0]\">Chapitre $row[0]</a></li>\n";
			else
				echo "						<li><a href=\"histoire.php?typ=$row[0]\">Chapitre $row[0]</a></li>\n";
		}
		echo "					</ul>\n";
		mysqli_close($idcom);
	}
}

function draw_colone_droite_histoire(){
	echo "					<p>Histoire</p>\n";
	$chap=$_POST["typ"];
	$subchap=$_POST["obj"];
	if (($chap!="")&&($_SESSION['acces']=="oui")&&($_SESSION['login']!="")) {
		$idcom=connexion_bd();
		$sql = mysqli_query($idcom,"SELECT * FROM Chapitres WHERE Numero = $chap");
		echo "					<ul id=\"ls_obj\">\n";
		while ($row = mysqli_fetch_row($sql)) {
			if ($chap=$row[1]){
				if ($subchap==$row[2])
					echo "						<li><a class=\"ob_actif\" href=\"histoire.php?typ=$chap&obj=$row[1]\">Sous Chapitre $row[1]</a></li>\n";
				else
					echo "						<li><a href=\"histoire.php?typ=$chap&obj=$row[1]\">Sous Chapitre $row[1]</a></li>\n";
			}
		}
		mysqli_close($idcom);
		echo "					</ul>\n";
	}
}

function draw_colone_centre_histoire(){
	echo "<div class=\"adress\">\n"; 
		echo "</div>\n";
	$chap=$_POST["typ"];
	$subchap=$_POST["obj"];
	echo "					<aside>\n";
	if (($chap!="")&&($subchap!="")&&($_SESSION['acces']=="oui")&&($_SESSION['login']!="")) {
		$idcom=connexion_bd();
		$sql = mysqli_query($idcom,"SELECT * FROM Chapitres WHERE Numero = $chap AND sousnumero = $subchap ");
		$row = mysqli_fetch_row($sql);
		echo "<h2>$row[3]</h2>";
		echo $row[4];
		mysqli_close($idcom);
	}else{
		echo "					<h2>Petit résumé de l'histoire d'Ayoaron</h2>\n";
		echo "					<p>Il y a près de 10000 ans, un peuple extraterrestre est passé sur la Terre. Ils ont alors commencé à discuter avec certains peuples humains et, ensemble, ils ont décidé de partir pour une autre planète en effaçant toutes traces de leur passage sur Terre pour ne pas que les autres hommes (nous, en quelques sorte) ne le sachent.</p>\n";
		echo "					<p>Après un très long voyage ils sont arrivés sur une planète dont les conditions de vie ressemblaient fortement à celles de la Terre, ils la baptisèrent Ayoaron. Les différences principales sont qu'elle a deux lunes et que le système a deux étoiles bleues (évidement, tout le reste du système est différent). Arrivés sur cette planète, les grands mages décidèrent d'isoler la Terre du reste de la galaxie par une barrière magique, empêchant quiconque d'aller sur la Terre ou même de l'observer et vice-versa. C'est pourquoi, aujourd'hui encore on ne connait rien de la vie dans la galaxie. Ils aménagèrent toutefois un passage reliant la Terre à Ayoaron.</p>\n";
		echo "					<p>De nombreuses guerres éclatèrent entre les hommes et d'autres espèces extraterrestres pour le contrôle de ce passage, et au fil du temps, la Terre est devenue une sorte de légende, un jardin d'Eden aux yeux de tous les peuples de la galaxie, y compris les hommes car seuls quelques individus bien particuliers font de temps en temps le voyage.</p>\n";
		echo "					<p>La dernière guerre en date, a laissé le peuple des hommes sous l'esclavage des Salagoronds (une sorte de croisement entre un crocodile et une araignée: une vraie saleté), mais ceux-ci n'ont jamais découvert le passage de la Terre. </p>\n";
		echo "					<p>De nos jours un jeune garçon sur la Terre découvre par hasard l'autre extrémité du passage et le traverse. Une chose étrange se produit durant son passage: il remonte le temps, de près de 1500 ans, et il se retrouve sur Ayoaron. Venant de la Terre, tout le monde le prend pour une sorte de dieu ou du moins un ange qui doit les libérer.</p>\n";
		echo "					<p>Après de multiples histoires et quelques apparitions sur la Terre, racontées dans les chapitres, les hommes ont enfin gagné la guerre. Cependant des poches de résistances sont encore bien en place et menace l'équilibre encore fragile du monde des hommes.</p>\n";
		echo "					<p>Les évenements du jeu se placent donc chronologiquement après ceux des chapitres!</p>\n";
	}
	echo "					</aside>\n";
}

?>