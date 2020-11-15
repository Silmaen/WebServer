<?PHP

require_once("fonctions_bd.php");

function draw_colone_gauche_univers(){
	$typ=$_POST["typ"];
	$obj=$_POST["obj"];
	$idcom=connexion_bd();
	$sql = mysqli_query($idcom,"SELECT * FROM obj_type ORDER BY ID ASC");
	echo "					<ul id=\"ls_type\">\n";
	while ($row = mysqli_fetch_row($sql)) {
		$counter = mysqli_fetch_array(mysqli_query($idcom,"SELECT COUNT(*) NBR_ENTREE FROM $row[2]"));
		if ($typ==$row[1])
			echo "						<li><a class=\"ty_actif\" href=\"univers.php?typ=$row[1]\">$row[1] ($counter[0])</a></li>\n";
		else
			echo "						<li><a href=\"univers.php?typ=$row[1]\">$row[1] ($counter[0])</a></li>\n";
	}
	echo "					</ul>\n";
	mysqli_close($idcom);
}

function draw_colone_droite_univers(){
	$typ=$_POST["typ"];
	$obj=$_POST["obj"];
	if ($typ!="") {
		$idcom=connexion_bd();
		$sql = mysqli_query($idcom,"SELECT * FROM obj_type WHERE nom LIKE \"$typ\"");
		$ndb = mysqli_fetch_row($sql);
		$sql = mysqli_query($idcom,"SELECT * FROM $ndb[2] ORDER BY nom ASC");
		echo "					<ul id=\"ls_obj\">\n";
		while ($row = mysqli_fetch_row($sql)) {
			if ($obj==$row[1])
				echo "						<li><a class=\"ob_actif\" href=\"univers.php?typ=$typ&obj=$row[1]\">$row[1]</a></li>\n";
			else
				echo "						<li><a href=\"univers.php?typ=$typ&obj=$row[1]\">$row[1]</a></li>\n";
		}
		mysqli_close($idcom);
		echo "					</ul>\n";
	}
}

function draw_colone_centre_univers(){
	$typ=$_POST["typ"];
	$obj=$_POST["obj"];
	require_once("fonctions_objets.php");
	echo "						<h1>Entrée de la base de données:</h1>\n";
	if ($typ!="") {
		$idcom=connexion_bd();
		if ($obj!="") {
			$sql = mysqli_query($idcom,"SELECT * FROM obj_type WHERE nom LIKE \"$typ\"");
			$ndb = mysqli_fetch_row($sql);
			$sql = mysqli_query($idcom,"SELECT * FROM $ndb[2] WHERE nom LIKE \"$obj\"");
			$row = mysqli_fetch_row($sql);
			draw_fiche_obj($typ,$row);
		}else{
			$sql = mysqli_query($idcom,"SELECT * FROM obj_type WHERE nom LIKE \"$typ\"");
			$ndb = mysqli_fetch_row($sql);
			$sql = mysqli_query($idcom,"SELECT * FROM $ndb[2] ORDER BY nom ASC");
			while ($row = mysqli_fetch_row($sql)) {
				draw_fiche_obj($typ,$row);
			}
		}
		mysqli_close($idcom);
	}
}

?>