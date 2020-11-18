<?PHP

function draw_fiche_obj($type,$rows){
	/*echo "					<article class=\"cadre_resultat\">
						<div class=\"nom_resultat\">
							<h1> $rows[1] </h1>
						</div>
						<div class=\"news_centre\">
							<p>$rows[2]</p> 
						</div>
					</article>\n";*/
	if ($type=="Planètes"){
		$typestr="planète";
		$IDstr="PLA".$rows[0];
	}
	if ($type=="Vaisseaux"){
		$typestr="vaisseau";
		$IDstr="VAI".$rows[0];
	}
	if ($type=="Etoiles"){
		$typestr="étoile";
		$IDstr="ETO".$rows[0];
	}
	if ($type=="Lunes"){
		$typestr="lune";
		$IDstr="LUN".$rows[0];
	}
	echo "					<article class=\"cadre_resultat\">
						<div class=\"restop\">
							<div class=\"resfich\">
								<ul>
									<li>Type: $typestr</li>
									<li>Nom: $rows[1]</li>
									<li>ID: $IDstr</li>
									<li>Race: $rows[2]</li>
								</ul>
							</div>
							<div class=\"resphoto\">
								<img src=\"$rows[3]\" width=\"100%\">
							</div>
						</div>
						<div class=\"resresume\">
							<h3>Resumé:</h3>
							$rows[4]
						</div>
						<div class=\"reshistoire\">
							<h3>Histoire:</h3>
							$rows[5]
						</div>
						<div class=\"rescarac\">
							<h3>Caractéristiques:</h3>
							$rows[6]
						</div>
					</article>\n";
}

?>