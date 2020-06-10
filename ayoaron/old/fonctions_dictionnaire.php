<?PHP

require_once("fonctions_bd.php");

/*
 * dessine la page du dictionnaire
 */
function draw_page_dictionnaire(){
	$motrech=$_POST["rechmot"];
	$_POST["rechmot"]="";
	if ($motrech!=""){
		$motrech = str_replace("*","%",$motrech);
		$motrech = str_replace("?","_",$motrech);
	}
	$motdefi=$_POST["rechdefi"];
	$_POST["rechdefi"]="";
	if ($motdefi!=""){
		$motdefi = str_replace("*","%",$motdefi);
		$motdefi = str_replace("?","_",$motdefi);
		$motdefi="%".$motdefi."%";
	}
	echo "					<aside>\n";
	echo "						<h2>Le dictionnaire</h2>\n";
	echo "						<form method=\"post\" action=\"langue.php?typ=Dictionnaire\">\n";
	echo "							<fieldset>\n";
	echo "								<legend>Rechercher:</legend>\n";
	echo "								<label>Rechercher mot <i>dequi ayoaronim</i></label>\n";
	echo "								<input type=\"text\" name=\"rechmot\"/>\n";
	echo "								<label>Rechercher dans les définitions</label>\n";
	echo "								<input type=\"text\" name=\"rechdefi\"/>\n";
	echo "								<input type=\"submit\" name=\"envoi\" value=\"OK\"/>\n";
	echo "								</legend>\n";
	echo "							</fieldset>\n";
	echo "						</form>\n";
	echo "						<br>\n";
	if ($motrech!=""){
		$idcom=connexion_bd();
		$sql = mysqli_query($idcom, "SELECT * FROM `dico_bd_mots` WHERE `radical` LIKE \"$motrech\"");
		while ($row = mysqli_fetch_row($sql)) {
			draw_definition($row);
		}
	}
	if ($motdefi!=""){
		$idcom=connexion_bd();
		$sql = mysqli_query($idcom, "SELECT * FROM `dico_bd_mots` WHERE `définition` LIKE \"$motdefi\"");
		while ($row = mysqli_fetch_row($sql)) {
			draw_definition($row);
		}
	}
	echo "					</aside>\n";
}

/*
 * fonction qui dessine le cadre d'une définition
 * à partir de la ligne sql.
 */
function draw_definition($row){
	$radical=$row[1];
	echo "					<article class=\"cadre_news\">\n";
	if ($row[2]=="verbe"){
		echo "						<p>".ecrit_alpha($radical."-")." (".ecrit_tourar($radical).") [".$row[6]."], ".$row[2]." </p>\n";
	}else{
		echo "						<p>".ecrit_alpha($radical)." (".ecrit_tourar($radical).") [".$row[6]."], ".$row[2]." </p>\n";
	}
	if ($row[3].$row[4]!="") {
		echo "						<p>";
		if ($row[3]!="")echo "Caractère de préfixe: ".ecrit_alpha($row[3])." (".ecrit_tourar($row[3]).") ";
		if ($row[4]!="")echo "Caractère de suffixe: ".ecrit_alpha($row[4])." (".ecrit_tourar($row[4]).") ";
		echo "						</p>\n";
	}
	echo "						<p>".$row[5]."</p><br>\n";
	if ($row[2]=="nom sexué") draw_declinaison_nomsex($radical,$row[3],$row[4]);
	if (($row[2]=="nom")||($row[2]=="nom propre")) draw_declinaison_nom($radical,$row[3],$row[4]);
	if ($row[2]=="pronom") draw_declinaison_nomsex($radical,$row[3],$row[4]);
	if ($row[2]=="verbe") draw_conjugaison($radical);
	echo "						<br>\n";
	echo "					</article>\n";
}

function draw_conjugaison($radical){
	echo "						<table>\n";
	echo "						<caption>Conjugaision du verbe ".ecrit_alpha($radical."-").", (".ecrit_tourar($radical).") :</caption>\n";
	echo "						<tr><th>						</th><th>Singulier																</th><th>Pair																		</th><th>Pluriel</th></tr>\n";
	echo "						<tr><td>Indicatif<br>Passé		</td><td>".ecrit_alpha($radical."u")."<br>".ecrit_tourar($radical."u")."		</td><td>".ecrit_alpha($radical."uar")."<br>".ecrit_tourar($radical."uar")."		</td><td>".ecrit_alpha($radical."ua")."<br>".ecrit_tourar($radical."ua")."</td></tr>\n";
	echo "						<tr><td>Indicatif<br>Présent	</td><td>".ecrit_alpha($radical."e")."<br>".ecrit_tourar($radical."e")."		</td><td>".ecrit_alpha($radical."ear")."<br>".ecrit_tourar($radical."ear")."		</td><td>".ecrit_alpha($radical."ea")."<br>".ecrit_tourar($radical."ea")."</td></tr>\n";
	echo "						<tr><td>Indicatif<br>Futur		</td><td>".ecrit_alpha($radical."o")."<br>".ecrit_tourar($radical."o")."		</td><td>".ecrit_alpha($radical."oar")."<br>".ecrit_tourar($radical."oar")."		</td><td>".ecrit_alpha($radical."oa")."<br>".ecrit_tourar($radical."oa")."</td></tr>\n";
	echo "						<tr><td>Impératif<br>Passé		</td><td>".ecrit_alpha($radical."ute")."<br>".ecrit_tourar($radical."ute")."	</td><td>".ecrit_alpha($radical."utear")."<br>".ecrit_tourar($radical."utear")."	</td><td>".ecrit_alpha($radical."utea")."<br>".ecrit_tourar($radical."utea")."</td></tr>\n";
	echo "						<tr><td>Impératif<br>Présent	</td><td>".ecrit_alpha($radical."ete")."<br>".ecrit_tourar($radical."ete")."	</td><td>".ecrit_alpha($radical."etear")."<br>".ecrit_tourar($radical."etear")."	</td><td>".ecrit_alpha($radical."etea")."<br>".ecrit_tourar($radical."etea")."</td></tr>\n";
	echo "						<tr><td>Impératif<br>Futur		</td><td>".ecrit_alpha($radical."ote")."<br>".ecrit_tourar($radical."ote")."	</td><td>".ecrit_alpha($radical."otear")."<br>".ecrit_tourar($radical."otear")."	</td><td>".ecrit_alpha($radical."otea")."<br>".ecrit_tourar($radical."otea")."</td></tr>\n";
	echo "						<tr><td>Conditionnel<br>Passé	</td><td>".ecrit_alpha($radical."ude")."<br>".ecrit_tourar($radical."ude")."	</td><td>".ecrit_alpha($radical."udear")."<br>".ecrit_tourar($radical."udear")."	</td><td>".ecrit_alpha($radical."udea")."<br>".ecrit_tourar($radical."udea")."</td></tr>\n";
	echo "						<tr><td>Conditionnel<br>Présent	</td><td>".ecrit_alpha($radical."ede")."<br>".ecrit_tourar($radical."ede")."	</td><td>".ecrit_alpha($radical."edear")."<br>".ecrit_tourar($radical."edear")."	</td><td>".ecrit_alpha($radical."edea")."<br>".ecrit_tourar($radical."edea")."</td></tr>\n";
	echo "						<tr><td>Conditionnel<br>Futur	</td><td>".ecrit_alpha($radical."ode")."<br>".ecrit_tourar($radical."ode")."	</td><td>".ecrit_alpha($radical."odear")."<br>".ecrit_tourar($radical."odear")."	</td><td>".ecrit_alpha($radical."odea")."<br>".ecrit_tourar($radical."odea")."</td></tr>\n";
	echo "						<tr><td>Subjonctif<br>Passé		</td><td>".ecrit_alpha($radical."uσe")."<br>".ecrit_tourar($radical."uσe")."	</td><td>".ecrit_alpha($radical."uσear")."<br>".ecrit_tourar($radical."uσear")."	</td><td>".ecrit_alpha($radical."uσea")."<br>".ecrit_tourar($radical."uσea")."</td></tr>\n";
	echo "						<tr><td>Subjonctif<br>Présent	</td><td>".ecrit_alpha($radical."eσe")."<br>".ecrit_tourar($radical."eσe")."	</td><td>".ecrit_alpha($radical."eσear")."<br>".ecrit_tourar($radical."eσear")."	</td><td>".ecrit_alpha($radical."eσea")."<br>".ecrit_tourar($radical."euσea")."</td></tr>\n";
	echo "						<tr><td>Subjonctif<br>Futur		</td><td>".ecrit_alpha($radical."oσe")."<br>".ecrit_tourar($radical."oσe")."	</td><td>".ecrit_alpha($radical."oσear")."<br>".ecrit_tourar($radical."oσear")."	</td><td>".ecrit_alpha($radical."oσea")."<br>".ecrit_tourar($radical."oσea")."</td></tr>\n";
	echo "						</table>\n";
}

function draw_declinaison_nom($radical,$precarac,$postcarac){
	echo "						<p>Liste des cas neutres:</p>\n";
	draw_tableau_declinaison($radical,$precarac,$postcarac);
}

function draw_declinaison_nomsex($radical,$precarac,$postcarac){
	echo "						<p>Liste des cas neutres:</p>\n";
	draw_tableau_declinaison($radical,$precarac,$postcarac);
	echo "						<br>\n";
	echo "						<p>Liste des cas masculins:</p>\n";
	draw_tableau_declinaison($radical.$postcarac."ün","","");
	echo "						<br>\n";
	echo "						<p>Liste des cas féminins:</p>\n";
	draw_tableau_declinaison($radical.$postcarac."in","","");
}

function draw_tableau_declinaison($radical,$precarac,$postcarac){
	echo "						<table>\n";
	echo "							<caption>".ecrit_alpha($radical)." (".ecrit_tourar($radical).")</caption>\n";
	echo "							<tbody>\n";
	echo "								<tr><th>cas</th><th>singulier</th><th>duel</th><th>pluriel</th></tr>\n";
	echo "								<tr><td>Nominatif</td>
<td>".ecrit_alpha($radical)."<br>".ecrit_tourar($radical)."</td>
<td>".ecrit_alpha($radical.$postcarac."ès")."<br>".ecrit_tourar($radical.$postcarac."ès")."</td>
<td>".ecrit_alpha($radical.$postcarac."er")."<br>".ecrit_tourar($radical.$postcarac."er")."</td></tr>\n";
	echo "								<tr><td>Accusatif</td>
<td>".ecrit_alpha($radical.$postcarac."òl")."<br>".ecrit_tourar($radical.$postcarac."òl")."</td>
<td>".ecrit_alpha($radical.$postcarac."òlès")."<br>".ecrit_tourar($radical.$postcarac."òlès")."</td>
<td>".ecrit_alpha($radical.$postcarac."òler")."<br>".ecrit_tourar($radical.$postcarac."òler")."</td></tr>\n";
	echo "								<tr><td>Datif</td>
<td>".ecrit_alpha($radical.$postcarac."id")."<br>".ecrit_tourar($radical.$postcarac."id")."</td>
<td>".ecrit_alpha($radical.$postcarac."òlès")."<br>".ecrit_tourar($radical.$postcarac."idès")."</td>
<td>".ecrit_alpha($radical.$postcarac."ider")."<br>".ecrit_tourar($radical.$postcarac."ider")."</td></tr>\n";
	echo "								<tr><td>Génitif</td>
<td>".ecrit_alpha($radical.$postcarac."im")."<br>".ecrit_tourar($radical.$postcarac."im")."</td>
<td>".ecrit_alpha($radical.$postcarac."òmès")."<br>".ecrit_tourar($radical.$postcarac."imès")."</td>
<td>".ecrit_alpha($radical.$postcarac."imer")."<br>".ecrit_tourar($radical.$postcarac."imer")."</td></tr>\n";
	echo "								<tr><td>Locatif</td>
<td>".ecrit_alpha($radical.$postcarac."af")."<br>".ecrit_tourar($radical.$postcarac."af")."</td>
<td>".ecrit_alpha($radical.$postcarac."òlès")."<br>".ecrit_tourar($radical.$postcarac."afès")."</td>
<td>".ecrit_alpha($radical.$postcarac."afer")."<br>".ecrit_tourar($radical.$postcarac."afer")."</td></tr>\n";
	echo "								<tr><td>Adjectif</td>
<td>".ecrit_alpha($radical.$postcarac."ëg")."<br>".ecrit_tourar($radical.$postcarac."ëg")."</td>
<td>".ecrit_alpha($radical.$postcarac."ëgès")."<br>".ecrit_tourar($radical.$postcarac."ëgès")."</td>
<td>".ecrit_alpha($radical.$postcarac."ëger")."<br>".ecrit_tourar($radical.$postcarac."ëger")."</td></tr>\n";
	echo "								<tr><td>Adverbe</td>
<td>".ecrit_alpha($radical.$postcarac."àt")."<br>".ecrit_tourar($radical.$postcarac."àt")."</td>
<td>".ecrit_alpha($radical.$postcarac."àtès")."<br>".ecrit_tourar($radical.$postcarac."àtès")."</td>
<td>".ecrit_alpha($radical.$postcarac."àter")."<br>".ecrit_tourar($radical.$postcarac."àter")."</td></tr>\n";
	echo "							</tbody>\n";
	echo "						</table>\n";
}

//=================================================================================
function ecrit_alpha($str){
	return "<i>".$str."</i>";
}

function ecrit_tourar($str){
	return "<q class=\"ayoaron\">".mot_conv_alph_tourar($str)."</q>";
}
/* 
 * fonction de convertion d'un mot depuis 
 * son écriture en alphabet transposé
 * vers la chaine à afficher en tourar
 */
function mot_conv_alph_tourar($mot_alpha){
	$len=strlen($mot_alpha);
	if ($len==0)return "";
	$car="";
	$pos=0;
	for($i=0;$i<$len;$i++){
		$car=$car.$mot_alpha[$i];
		if (is_voyelle($car)){
			$tab_alpha[$pos]=$car;
			$pos++;
			$car="";
		}else if (is_consonne($car)){
			$tab_alpha[$pos]=$car;
			$pos++;
			$car="";
		}
		if (strlen($car)==2) $car="";
	}
	$len=$pos;
	$chaine="";
	$ivoyelle=true;
	for($i=0;$i<$len;$i++){
		if (is_voyelle($tab_alpha[$i])){
			if ($ivoyelle) {
				if (($i+1)==$len){
					$chaine=$chaine."#".$tab_alpha[$i];
				}else{
					if (is_consonne($tab_alpha[$i+1])){
						$chaine.=down_acc($tab_alpha[$i]);
					}else{
						$chaine=$chaine."#".$tab_alpha[$i];
					}
				}
			}else{
				$chaine=$chaine.$tab_alpha[$i];
			}
			$ivoyelle=true;
		}else if (is_consonne($tab_alpha[$i])){
			$ivoyelle=false;
			$chaine=$chaine.cons_to_toura($tab_alpha[$i]);
		}
	}
	return $chaine;
}

/* 
 * fonction de convertion d'un mot depuis 
 * son écriture en alphabet ttourar
 * vers la chaine à afficher en transposé
 */
function mot_conv_tourar_alpha($mot_alpha){
	$len=strlen($mot_alpha);
	if ($len==0) return "";
	$tab_alpha=explode("",$mot_alpha);
	$chaine="";
	$ivoyelle=true;
	for($i=0;$i<$len;$i++){
		if (is_accent($tab_alpha[$i])) $chaine.=strtolower($tab_alpha[$i]);
		if (is_toura($tab_alpha[$i])) $chaine.=toura_to_cons($tab_alpha[$i]);
	}
	return $chaine;
}

function is_voyelle($voy){
	if ($voy=="a") return true;
	if ($voy=="à") return true;
	if ($voy=="e") return true;
	if ($voy=="ë") return true;
	if ($voy=="è") return true;
	if ($voy=="é") return true;
	if ($voy=="o") return true;
	if ($voy=="ô") return true;
	if ($voy=="ò") return true;
	if ($voy=="ü") return true;
	if ($voy=="u") return true;
	if ($voy=="ù") return true;
	if ($voy=="i") return true;
	if ($voy=="î") return true;
	return false;
}

function down_acc($voy){
	if ($voy=="a") return "A";
	if ($voy=="à") return "À";
	if ($voy=="e") return "E";
	if ($voy=="ë") return "Ë";
	if ($voy=="è") return "È";
	if ($voy=="é") return "É";
	if ($voy=="o") return "O";
	if ($voy=="ô") return "Ô";
	if ($voy=="ò") return "Ò";
	if ($voy=="ü") return "Ü";
	if ($voy=="u") return "U";
	if ($voy=="ù") return "Ù";
	if ($voy=="i") return "I";
	if ($voy=="î") return "Î";
	return "";
}

function is_consonne($con){
	if ($con=="b")return true;
	if (($con=="c")||($con=="k"))return true;
	if ($con=="d")return true;
	if ($con=="f")return true;
	if ($con=="g")return true;
	if ($con=="j")return true;
	if ($con=="l")return true;
	if ($con=="m")return true;
	if ($con=="n")return true;
	if ($con=="p")return true;
	if ($con=="r")return true;
	if ($con=="ρ")return true;
	if ($con=="h")return true;
	if ($con=="s")return true;
	if ($con=="t")return true;
	if ($con=="v")return true;
	if ($con=="w")return true;
	if ($con=="y")return true;
	if ($con=="z")return true;
	if ($con=="x")return true;
	if ($con=="τ")return true;
	if ($con=="φ")return true;
	if ($con=="δ")return true;
	if ($con=="Δ")return true;
	if ($con=="χ")return true;
	if ($con=="ç")return true;
	if ($con=="q")return true;
	if ($con=="ξ")return true;
	if ($con=="ζ")return true;
	if ($con=="ϕ")return true;
	if ($con=="σ")return true;
	if ($con=="ς")return true;
	if ($con=="ψ")return true;
	if ($con=="ω")return true;
	if ($con=="γ")return true;
	if ($con=="θ")return true;
	if ($con=="μ")return true;
	if ($con=="υ")return true;
	if ($con=="_")return true;
	return false;
}

function is_accent($acc){
	if ($acc=="a") return true;
	if ($acc=="A") return true;
	if ($acc=="à") return true;
	if ($acc=="À") return true;
	if ($acc=="e") return true;
	if ($acc=="E") return true;
	if ($acc=="ë") return true;
	if ($acc=="Ë") return true;
	if ($acc=="è") return true;
	if ($acc=="È") return true;
	if ($acc=="é") return true;
	if ($acc=="É") return true;
	if ($acc=="o") return true;
	if ($acc=="O") return true;
	if ($acc=="ô") return true;
	if ($acc=="Ô") return true;
	if ($acc=="ò") return true;
	if ($acc=="Ò") return true;
	if ($acc=="ü") return true;
	if ($acc=="Ü") return true;
	if ($acc=="u") return true;
	if ($acc=="U") return true;
	if ($acc=="ù") return true;
	if ($acc=="Ù") return true;
	if ($acc=="i") return true;
	if ($acc=="I") return true;
	if ($acc=="î") return true;
	if ($acc=="Î") return true;
	return false;
}

function is_toura($tou){
	if ($con=="b")return true;
	if ($con=="c")return true;
	if ($con=="d")return true;
	if ($con=="f")return true;
	if ($con=="g")return true;
	if ($con=="j")return true;
	if ($con=="l")return true;
	if ($con=="m")return true;
	if ($con=="n")return true;
	if ($con=="p")return true;
	if ($con=="r")return true;
	if ($con=="k")return true;
	if ($con=="h")return true;
	if ($con=="s")return true;
	if ($con=="t")return true;
	if ($con=="v")return true;
	if ($con=="w")return true;
	if ($con=="y")return true;
	if ($con=="z")return true;
	if ($con=="x")return true;
	if ($con=="T")return true;
	if ($con=="R")return true;
	if ($con=="D")return true;
	if ($con=="H")return true;
	if ($con=="C")return true;
	if ($con=="K")return true;
	if ($con=="q")return true;
	if ($con=="P")return true;
	if ($con=="B")return true;
	if ($con=="F")return true;
	if ($con=="V")return true;
	if ($con=="S")return true;
	if ($con=="L")return true;
	if ($con=="X")return true;
	if ($con=="G")return true;
	if ($con=="Q")return true;
	if ($con=="N")return true;
	if ($con=="M")return true;
	if ($con=="_")return true;
	return "";
}

function acc_to_voy($acc){
	if ($acc=="a") return "a";
	if ($acc=="A") return "a";
	if ($acc=="à") return "à";
	if ($acc=="À") return "à";
	if ($acc=="e") return "e";
	if ($acc=="E") return "e";
	if ($acc=="ë") return "ë";
	if ($acc=="Ë") return "ë";
	if ($acc=="è") return "è";
	if ($acc=="È") return "è";
	if ($acc=="é") return "é";
	if ($acc=="É") return "é";
	if ($acc=="o") return "o";
	if ($acc=="O") return "o";
	if ($acc=="ô") return "ô";
	if ($acc=="Ô") return "ô";
	if ($acc=="ò") return "ò";
	if ($acc=="Ò") return "ò";
	if ($acc=="ü") return "ü";
	if ($acc=="Ü") return "Ü";
	if ($acc=="u") return "u";
	if ($acc=="U") return "u";
	if ($acc=="ù") return "ù";
	if ($acc=="Ù") return "ù";
	if ($acc=="i") return "i";
	if ($acc=="I") return "i";
	if ($acc=="î") return "î";
	if ($acc=="Î") return "î";
	return "";
}

function cons_to_toura($con){
	if ($con=="b")return "b";
	if (($con=="c")||($con=="k"))return "c";
	if ($con=="d")return "d";
	if ($con=="f")return "f";
	if ($con=="g")return "g";
	if ($con=="j")return "j";
	if ($con=="l")return "l";
	if ($con=="m")return "m";
	if ($con=="n")return "n";
	if ($con=="p")return "p";
	if ($con=="r")return "r";
	if ($con=="ρ")return "k";
	if ($con=="h")return "h";
	if ($con=="s")return "s";
	if ($con=="t")return "t";
	if ($con=="v")return "v";
	if ($con=="w")return "w";
	if ($con=="y")return "y";
	if ($con=="z")return "z";
	if ($con=="x")return "x";
	if ($con=="τ")return "T";
	if ($con=="φ")return "R";
	if ($con=="δ")return "D";
	if ($con=="Δ")return "H";
	if ($con=="χ")return "C";
	if ($con=="ç")return "K";
	if ($con=="q")return "q";
	if ($con=="ξ")return "P";
	if ($con=="ζ")return "B";
	if ($con=="ϕ")return "F";
	if ($con=="σ")return "V";
	if ($con=="ς")return "S";
	if ($con=="ψ")return "L";
	if ($con=="ω")return "X";
	if ($con=="γ")return "G";
	if ($con=="θ")return "Q";
	if ($con=="μ")return "N";
	if ($con=="υ")return "M";
	if ($con=="_")return "_";
	return "";
}

function toura_to_cons($con){
	if ($con=="b")return "b";
	if ($con=="c")return "c";
	if ($con=="d")return "d";
	if ($con=="f")return "f";
	if ($con=="g")return "g";
	if ($con=="j")return "j";
	if ($con=="l")return "l";
	if ($con=="m")return "m";
	if ($con=="n")return "n";
	if ($con=="p")return "p";
	if ($con=="r")return "r";
	if ($con=="k")return "ρ";
	if ($con=="h")return "h";
	if ($con=="s")return "s";
	if ($con=="t")return "t";
	if ($con=="v")return "v";
	if ($con=="w")return "w";
	if ($con=="y")return "y";
	if ($con=="z")return "z";
	if ($con=="x")return "x";
	if ($con=="T")return "τ";
	if ($con=="R")return "φ";
	if ($con=="D")return "δ";
	if ($con=="H")return "Δ";
	if ($con=="C")return "χ";
	if ($con=="K")return "ç";
	if ($con=="q")return "q";
	if ($con=="P")return "ξ";
	if ($con=="B")return "ζ";
	if ($con=="F")return "ϕ";
	if ($con=="V")return "σ";
	if ($con=="S")return "ς";
	if ($con=="L")return "ψ";
	if ($con=="X")return "ω";
	if ($con=="G")return "γ";
	if ($con=="Q")return "θ";
	if ($con=="N")return "μ";
	if ($con=="M")return "υ";
	if ($con=="_")return "_";
	return "";
}

?>