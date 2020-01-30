<?PHP

require_once("fonctions_bd.php");
require_once("fonctions_dictionnaire.php");

function draw_colone_gauche_langue(){
	echo "					<p>Langue</p>\n";
	$typ=$_POST["typ"];
	$obj=$_POST["obj"];
	$idcom=connexion_bd();
	$sql = mysqli_query($idcom,"SELECT * FROM lang_type ORDER BY numero ASC");
	echo "					<ul id=\"ls_type\">\n";
	while ($row = mysqli_fetch_row($sql)) {
		$counter = mysqli_fetch_array(mysqli_query($idcom,"SELECT COUNT(*) NBR_ENTREE FROM $row[1]"));
		if ($typ==$row[0])
			echo "						<li><a class=\"ty_actif\" href=\"langue.php?typ=$row[0]\">$row[0]</a></li>\n";
		else
			echo "						<li><a href=\"langue.php?typ=$row[0]\">$row[0]</a></li>\n";
	}
	echo "					</ul>\n";
	mysqli_close($idcom);
}

function draw_colone_droite_langue(){
	echo "					<p>Langue</p>\n";
	$typ=$_POST["typ"];
	$obj=$_POST["obj"];
	if (($typ!="")&&($type!="Alphabet")&&($type!="Dictionnaire")) {
		$idcom=connexion_bd();
		$sql = mysqli_query($idcom,"SELECT * FROM lang_type WHERE nom LIKE \"$typ\"");
		$ndb = mysqli_fetch_row($sql);
		$sql = mysqli_query($idcom,"SELECT * FROM $ndb[1] ORDER BY numero ASC");
		echo "					<ul id=\"ls_obj\">\n";
		while ($row = mysqli_fetch_row($sql)) {
			if ($obj==$row[0])
				echo "						<li><a class=\"ob_actif\" href=\"langue.php?typ=$typ&obj=$row[0]\">$row[0]</a></li>\n";
			else
				echo "						<li><a href=\"langue.php?typ=$typ&obj=$row[0]\">$row[0]</a></li>\n";
		}
		mysqli_close($idcom);
		echo "					</ul>\n";
	}
}

function draw_colone_centre_langue(){
	$typ=$_POST["typ"];
	$obj=$_POST["obj"];
	if ($typ=="Dictionnaire") {
		draw_page_dictionnaire();
	}else if ($typ=="Citations") {
		draw_page_citation();
	}else if ($typ!="") {
		$idcom=connexion_bd();
		echo "					<aside>\n";
		echo "					<h2>La Grammaire</h2>\n";
		if ($obj!="") {
			$sql = mysqli_query($idcom,"SELECT * FROM lang_type WHERE nom LIKE \"$typ\"");
			$ndb = mysqli_fetch_row($sql);
			$sql = mysqli_query($idcom,"SELECT * FROM $ndb[1] WHERE nom LIKE \"$obj\"");
			$row = mysqli_fetch_row($sql);
			echo $row[1];
		}else{
			if ($typ=="L'alphabet") draw_chapitre_Alphabet();
			if ($typ=="La phrase")draw_chapitre_Phrase();
			echo "					<br><p>Veuillez selectionner une catégorie.</p>\n";
			echo "					</aside>\n";
		}
		mysqli_close($idcom);
	}else{
		echo "					<aside>\n";
		echo "					<h2>Le deqi ayoaronim</h2>\n";
		echo "					<p>Il s'agit de la langue utilisée par les hommes à travers toute la galaxie. Dans cette rubrique, vous trouverez tout pour lire et comprendre cette langue.</p>";
		echo "					</aside>\n";
	}
}

function draw_page_citation(){
	$idcom=connexion_bd();
	$sql = mysqli_query($idcom,"SELECT * FROM bd_citation ");
	while ($row = mysqli_fetch_row($sql)){
		echo "					<aside>\n";
		echo "						<article class=\"cadre_news\">\n";
		echo $row[1]."\n";
		echo "						</article>\n";
		echo "					</aside>\n";
	}
	mysqli_close($idcom);
}

function draw_chapitre_Alphabet(){
	echo "					<p>Le <i>deqi ayoaronim</i> s’écrit normalement avec les <i>turaer</i> (<q class=\"ayoaron\">turaEr</q>  les lettres, les consonnes) cependant, une translation en caractère latin existe et est présenté ici. Chaque <i>tura</i> représente une consonne, et une consonne, une manière de prononcer. La sonorité est donnée par le <i>cèra</i> (<q class=\"ayoaron\">cèra</q> l’accent, la voyelle).</p>\n";
	echo "					<p>Il n’y a pas de notion de majuscule ou minuscules. On commence par la notion de ‘porte-voyelle’ : <q class=\"ayoaron\">#</q> (caractère utf8 : #). Il s’agit d’une consonne sans sons particulier servant simplement à écrire le son d’une voyelle.</p>\n";
	echo "					<p>La voyelle est une manière de prononcer une consonne. Il est écrit comme un accent sur la consonne. Lorsque l’accent est en dessous de la voyelle, la voyelle est prononcée avant la consonne, lorsque l’accent est au dessus de la consonne, il est prononcer avec la consonne lui donnant un couleur.</p>\n";
}

function draw_chapitre_Phrase(){
	echo "					<p>Une phrase est une suite logique de mots. La fonction du mot est donnée par ses préfixes et suffixes. Ces formes varient en fonction du type du mot.</p>\n";
	echo "					<br><ul>Voici la liste des fonctions des mots :\n";
	echo "					<li>Nominatif	(qui ou quoi)</li>\n";
	echo "					<li>Verbal		(quelle action et dans quelle situation temporelle)</li>\n";
	echo "					<li>Accusatif	(qui ou quel est l’objet de l’action)</li>\n";
	echo "					<li>Datif		(à qui ou à quoi se rapporte l’action)</li>\n";
	echo "					<li>Génitif		(marque de possession)</li>\n";
	echo "					<li>Locatif	(où l’action est mené)</li>\n";
	echo "					<li>Adjectif	(qualifiant les formes hormis la forme verbal)</li>\n";
	echo "					<li>Adverbe	(qualifiant la forme verbale)</li></ul><br>\n";
	echo "					<ul>Le ton de la phrase est donné par les marques de début et de fin de phrase. Ces tons sont :\n";
	echo "					<li>Affirmation</li>\n";
	echo "					<li>Question</li>\n";
	echo "					<li>Exclamation</li>\n";
	echo "					<li>Ordre</li></ul><br>\n";
	echo "					<p>Des caractères de séparation permettent de différentier les différents blocs de la phrase.</p>\n";
}


?>