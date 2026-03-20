(* ::Package:: *)

(* ::Text:: *)
(*Import DRalgo and group math (in paclet form, needs DRalgo 1.3+*)


SetDirectory[NotebookDirectory[]];
<<DRalgo`DRalgo`


(* ::Text:: *)
(*Import helper functions and setup export path*)


Get["DRalgoToBLOOPHelper.m"]
(*Fresh added so it doesn't overwrite the old expression files*)
exportPath = "../../Build/Z2_3HDM/DRalgoOutputFiles";


(* ::Text:: *)
(*Extra things needed for BLOOP not given by DRalgo*)


exportUTF8[exportPath<>"/BoundedConditions.txt",
{\[Lambda]11>0,
\[Lambda]22>0,
\[Lambda]33>0,
\[Lambda]12 + min[0, \[Lambda]12p - 2*Sqrt[\[Lambda]1Re^2 + \[Lambda]1Im^2] ] > -2*sqrt[\[Lambda]11*\[Lambda]22],
\[Lambda]31 + min[0, \[Lambda]31p - 2*Sqrt[\[Lambda]3Re^2 + \[Lambda]3Im^2] ] > -2*sqrt[\[Lambda]11*\[Lambda]33],
\[Lambda]23 + min[0, \[Lambda]23p - 2*Sqrt[\[Lambda]2Re^2 + \[Lambda]2Im^2] ] > -2*sqrt[\[Lambda]22*\[Lambda]33],
sqrt[\[Lambda]33]*(\[Lambda]12 + min[0, \[Lambda]12p - 2*Sqrt[\[Lambda]1Re^2 + \[Lambda]1Im^2] ]) + sqrt[\[Lambda]11]*(\[Lambda]23 + min[0, \[Lambda]23p - 2*Sqrt[\[Lambda]2Re^2 + \[Lambda]2Im^2] ]) + sqrt[\[Lambda]22]*(\[Lambda]31 + min[0, \[Lambda]31p - 2*Sqrt[\[Lambda]3Re^2 + \[Lambda]3Im^2] ]) >= 0 ||
\[Lambda]33*(\[Lambda]12 + min[0, \[Lambda]12p - 2*Sqrt[\[Lambda]1Re^2 + \[Lambda]1Im^2] ])^2 + \[Lambda]11*(\[Lambda]23 + min[0, \[Lambda]23p - 2*Sqrt[\[Lambda]2Re^2 + \[Lambda]2Im^2] ])^2 + \[Lambda]22*(\[Lambda]31 + min[0, \[Lambda]31p - 2*Sqrt[\[Lambda]3Re^2 + \[Lambda]3Im^2] ])^2 - \[Lambda]11*\[Lambda]22*\[Lambda]33 - 2*(\[Lambda]12 + min[0, \[Lambda]12p - 2*Sqrt[\[Lambda]1Re^2 + \[Lambda]1Im^2] ])*(\[Lambda]31 + min[0, \[Lambda]31p - 2*Sqrt[\[Lambda]3Re^2 + \[Lambda]3Im^2] ])*(\[Lambda]23 + min[0, \[Lambda]23p - 2*Sqrt[\[Lambda]2Re^2 + \[Lambda]2Im^2] ]) < 0
}];


(* ::Section::Closed:: *)
(*Model*)


(*See 1909.09234 [hep-ph], eq (1) *)
Group={"SU3","SU2","U1"};
RepAdjoint={{1,1},{2},0};
HiggsDoublet1={{{0,0},{1},1/2},"C"};
HiggsDoublet2={{{0,0},{1},1/2},"C"};
HiggsDoublet3={{{0,0},{1},1/2},"C"};
RepScalar={HiggsDoublet1,HiggsDoublet2,HiggsDoublet3};

ClearAll[g1, g2, g3];
GaugeCouplings={g3,g2,g1};


Rep1={{{1,0},{1},1/6},"L"};
Rep2={{{1,0},{0},2/3},"R"};
Rep3={{{1,0},{0},-1/3},"R"};
Rep4={{{0,0},{1},-1/2},"L"};
Rep5={{{0,0},{0},-1},"R"};
RepFermion1Gen={Rep1,Rep2,Rep3,Rep4,Rep5};
RepFermion3Gen={RepFermion1Gen,RepFermion1Gen,RepFermion1Gen}//Flatten[#,1]&;


(* ::Text:: *)
(*The input for the gauge interactions toDRalgo are then given by*)


{gvvv,gvff,gvss,\[CapitalLambda]1,\[CapitalLambda]3,\[CapitalLambda]4,\[Mu]ij,\[Mu]IJ,\[Mu]IJC,Ysff,YsffC}=AllocateTensors[Group,RepAdjoint,GaugeCouplings,RepFermion3Gen,RepScalar];
(** Note that AllocateTensors[] brings some GroupMath symbols to the global namespace. And these are only removed later when calling ImportModelDRalgo...**)


(* ::Text:: *)
(*The first element is the vector self - interaction matrix :*)


(** Here just list all possible gauge-invariant operators containing 2 doublets **)
(** DRalgo notation is that \[Phi]1\[Phi]2^+ = \!\(
\*SubsuperscriptBox[\(\[Phi]\), \(2\), \(\[Dagger]\)]
\*SubscriptBox[\(\[Phi]\), \(1\)]\ in\ standard\ \(notation . \ \nSo\)\ careful\ here\ to\ make\ sure\ imaginary\ parts\ match\ to\ the\ potential\ in\ our\ draft\) **)
(** I have changed the notation a lot from DRalgo's example 3HDM file. 
My notation for doublet products is \[Phi]ij, where first index is the conjugated doublet **)

InputInv={{1,1},{True,False}}; (*\[Phi]1 \[Phi]1^\[Dagger]*)
\[Phi]11=CreateInvariant[Group,RepScalar,InputInv][[1]]//Simplify//FullSimplify;

InputInv={{2,2},{True,False}}; (*\[Phi]2 \[Phi]2^\[Dagger]*)
\[Phi]22=CreateInvariant[Group,RepScalar,InputInv][[1]]//Simplify//FullSimplify;

InputInv={{3,3},{True,False}}; (*\[Phi]3 \[Phi]3^\[Dagger]*)
\[Phi]33=CreateInvariant[Group,RepScalar,InputInv][[1]]//Simplify//FullSimplify;

InputInv={{1,2},{True,False}}; (*\[Phi]1\[Phi]2^\[Dagger]*)
\[Phi]21=CreateInvariant[Group,RepScalar,InputInv][[1]]//Simplify//FullSimplify;

InputInv={{2,1},{True,False}};(*\[Phi]2\[Phi]1^\[Dagger]*)
\[Phi]12=CreateInvariant[Group,RepScalar,InputInv][[1]]//Simplify//FullSimplify;

InputInv={{1,3},{True,False}}; (*\[Phi]1\[Phi]3^\[Dagger]*)
\[Phi]31=CreateInvariant[Group,RepScalar,InputInv][[1]]//Simplify//FullSimplify;

InputInv={{3,1},{True,False}};(*\[Phi]3\[Phi]1^\[Dagger]*)
\[Phi]13=CreateInvariant[Group,RepScalar,InputInv][[1]]//Simplify//FullSimplify;

InputInv={{2,3},{True,False}}; (*\[Phi]2\[Phi]3^\[Dagger]*)
\[Phi]32=CreateInvariant[Group,RepScalar,InputInv][[1]]//Simplify//FullSimplify;

InputInv={{3,2},{True,False}};(*\[Phi]3\[Phi]2^\[Dagger]*)
\[Phi]23=CreateInvariant[Group,RepScalar,InputInv][[1]]//Simplify//FullSimplify;


(* Define some shorthands for complex parameters. DRalgo performs better if real/imag parts are used separately. *)
\[Mu]12sq = \[Mu]12sqRe + I*\[Mu]12sqIm;
\[Mu]12sqConj = Conjugate[\[Mu]12sq]//ComplexExpand;

\[Lambda]1 = \[Lambda]1Re + I*\[Lambda]1Im;
\[Lambda]1Conj = Conjugate[\[Lambda]1]//ComplexExpand;
\[Lambda]2 = \[Lambda]2Re + I*\[Lambda]2Im;
\[Lambda]2Conj = Conjugate[\[Lambda]2]//ComplexExpand;
\[Lambda]3 = \[Lambda]3Re + I*\[Lambda]3Im;
\[Lambda]3Conj = Conjugate[\[Lambda]3]//ComplexExpand;


(* Quadratic terms. Careful with complex conjugates *)
VMass=-\[Mu]1sq*\[Phi]11 - \[Mu]2sq*\[Phi]22 - \[Mu]3sq*\[Phi]33 - \[Mu]12sq*\[Phi]12 - \[Mu]12sqConj*\[Phi]21 // Simplify // Expand; (* simplify to get rid of imag units *)


\[Mu]ij=GradMass[VMass]//Simplify//SparseArray;


(** Def. quartic terms. Careful with complex conjugates **) 
QuarticTerm1 = \[Lambda]11*\[Phi]11^2 + \[Lambda]22*\[Phi]22^2 + \[Lambda]33*\[Phi]33^2;
QuarticTerm2 = \[Lambda]12*\[Phi]11*\[Phi]22 + \[Lambda]23*\[Phi]22*\[Phi]33 + \[Lambda]31*\[Phi]33*\[Phi]11;
QuarticTerm3 = \[Lambda]12p*\[Phi]12*\[Phi]21 + \[Lambda]23p*\[Phi]23*\[Phi]32 + \[Lambda]31p*\[Phi]31*\[Phi]13;
QuarticTerm4 = \[Lambda]1*\[Phi]12^2 + \[Lambda]2*\[Phi]23^2 + \[Lambda]3*\[Phi]31^2;
(* Hermitian conjugate of QuarticTerm4. Just adding it as ConjugateTranspose[...] didn't work, DRalgo just seemed to get stuck. *)
QuarticTerm5 = \[Lambda]1Conj*\[Phi]21^2 + \[Lambda]2Conj*\[Phi]32^2 + \[Lambda]3Conj*\[Phi]13^2;
VQuartic=QuarticTerm1 + QuarticTerm2 + QuarticTerm3 + QuarticTerm4 + QuarticTerm5 // Simplify // Expand; (* simplify to get rid of imag units *)
\[CapitalLambda]4=GradQuartic[VQuartic];


InputInv={{3,1,2},{False,False,True}}; 
YukawaDoublet3=CreateInvariantYukawa[Group,RepScalar,RepFermion3Gen,InputInv][[1]]//Simplify;

Ysff=-GradYukawa[yt3*YukawaDoublet3];
YsffC=SparseArray[Simplify[Conjugate[Ysff]//Normal,Assumptions->{yt3>0}]];


(* ::Section:: *)
(*Dimensional Reduction*)


(* ::Text:: *)
(*Parametric accuracy goal of the EFT matchings need to be specified already in ImportModelDRalgo[] (Mode option). We need mode 2 to do 2 loop/NNLO effective potential*)


(** Normalization4D flag = preserve 4D units so that the EFT path integral weight is e^{-S/T} 
BLOOP assumes 3D units and all results are dimensionless ratios so I don't think we need to support this flag
AutoRG->True means that 3D running is built in to the matching.
This leads to the 3D masses being functions of two scales which is a pain. 
Easy to just have AutoRG->False and do the RG running manually in an additional stage. **)
ImportModelDRalgo[Group,gvvv,gvff,gvss,\[CapitalLambda]1,\[CapitalLambda]3,\[CapitalLambda]4,\[Mu]ij,\[Mu]IJ,\[Mu]IJC,Ysff,YsffC,Verbose->False, Mode->2, Normalization4D->False, AutoRG->False];


betaFunctions4DUnsquared = BetaFunctions4D[]/.{(x_^2 -> y_) :> (x -> y/(2*x))};
exportUTF8[exportPath<>"/BetaFunctions4D.txt", betaFunctions4DUnsquared];


PerformDRhard[];


couplingsSoft = PrintCouplings[];
temporalScalarCouplings = PrintTemporalScalarCouplings[];
(** For Debyes we only take LO result, NLO not needed since we integrate these out anyway.
If NLO part needed be sure to use combineSubstRules as is done in scalarMasses **)
debyeMasses = PrintDebyeMass["LO"];
scalarMasses = combineSubstRules[PrintScalarMass["LO"], PrintScalarMass["NLO"]];


(*DRalgo gives temporal couplings with [] which is a function call which makes things awkward so remove the []*)
\[Lambda]VL[i_]:=ToExpression["\[Lambda]VL"<>ToString[i]];
\[Lambda]VLL[i_]:=ToExpression["\[Lambda]VLL"<>ToString[i]];


(* ::Text:: *)
(*Setting the scales. *)
(*Each scale (and Lb and Lf) can be a function of T and parameters of the scale above it**)
(*E.g. the soft scale could be g1(hard)*T We*)
(**In theory - I should really test that*)


hardScale = N[4\[Pi]*Exp[-EulerGamma]*T];
softScale = T;
ultraSoftScale = T;
lb=0;
lf=N[4Log[2]];
exportUTF8[exportPath<>"/HardScale.txt", hardScale];


(* Removing the suffixes makes it easier to do in place updating in BLOOP (more efficent) *)
(* NOTE: Because we take the sqrt of the gauge couplings there is a sign ambiguity - we only consider the positive root
In theory this could also make the gauge couplings complex (very bad) but this would likely be in a non-pert regime i.e.
g1 = sqrt(T)*g1*sqrt[1 - ((g1^2) (3Lb+40Lf) )/(96 \[Pi]^2)] - the correction has to be larger than 1*) 
hardToSoft = removeDRalgoSuffixes[sqrtSubRules[Join[couplingsSoft, temporalScalarCouplings, debyeMasses, scalarMasses]]]/.Lb->lb/.Lf->lf;
exportUTF8[exportPath<>"/HardToSoft.txt", hardToSoft];


softParamsRGE = removeDRalgoSuffixes[solveRunning3D[BetaFunctions3DS[], softScale, hardScale]];
exportUTF8[exportPath<>"/SoftScaleRGE.txt", softParamsRGE];


(* ::Subsection:: *)
(*Soft -> Ultrasoft matching*)


PerformDRsoft[{}];
couplingsUS = PrintCouplingsUS[];
scalarMassesUS = combineSubstRules[PrintScalarMassUS["LO"], PrintScalarMassUS["NLO"]];
ultrasoftScaleParams = removeDRalgoSuffixes[sqrtSubRules[Join[couplingsUS, scalarMassesUS]]]/. \[Mu]3->softScale;
exportUTF8[exportPath<>"/SoftToUltraSoft.txt", ultrasoftScaleParams];


ultraSoftParamsRGE = removeDRalgoSuffixes[solveRunning3D[BetaFunctions3DUS[], ultraSoftScale, softScale]];
exportUTF8[exportPath<>"/UltraSoftScaleRGE.txt", ultraSoftParamsRGE];


(* ::Section:: *)
(*Vector and scalar mass matrices*)


(* ::Subsection:: *)
(*Specify background fields and init DRalgo stuff*)


UseUltraSoftTheory[];
DefineNewTensorsUS[\[Mu]ij,\[CapitalLambda]4,\[CapitalLambda]3,gvss,gvvv]; 
PrintScalarRepPositions[](** This is supposed to tell which index is which field, but it's cryptic... **)

(** DRalgo ordering: real parts go before imag parts, and this is repeated 3 times (because we have 3 complex doublets). 
So the "usual" place for BG field is second index in each doublet**)

backgroundFieldsFull = {(*\[Phi]1*)0, v1, 0, 0,(*\[Phi]2*)0, v2, 0, 0, (*\[Phi]3*)0, v3, 0, 0}//SparseArray; 
DefineVEVS[backgroundFieldsFull];


(* ::Subsection:: *)
(*Diagonalizing scalar mass matrix*)


(* ::Text:: *)
(*Finding the diagonalizing matrix analytically is likely impossible, so we brute force this by giving DRalgo a symbolic 12x12 matrix with unknown symbols and compute the Veff in terms of those symbols. For masses we give an unknown diagonal matrix. These unknown are field-dependent so we must solve them numerically every time the potential is evaluated. *)
(**)
(*Note that using unknown symbols in the rotation matrix means that DRalgo will compute the effective potential in what is effectively a non-diagonal field basis, ie. there is quadratic mixing. But all the mixing effects vanish when numerical values are fixed by diagonalization conditions later on. (And I believe DRalgo ignores quadratic vertices anyway, but have not confirmed this). *)
(**)
(*Now, there are some optimizations that we can do. For example with the 3-field configuration defined above, the mass matrix can be brought into block-diagonal form by permuting the fields. This reduces the problem to diagonalization of two 6x6 matrices which is faster. We use this approach here; the required 12x12 rotation then has zeros in many places so DRalgo has easier time working with it.*)


scalarMM = PrintTensorsVEV[1]//Normal//Simplify; (* Scalar mass matrix, simplify to get rid of possible imaginary units *)


(* ::Subsubsection:: *)
(*Permute scalars to make mass matrix block-diagonal *)


(* Permutation matrix swaps the following rows and colums: 2<->11, 4<->9,6<->7  to get a block diagonal matrix. 
These are the minimal swaps to get a block diagonal matrix, and conviently leave the permutation symmetric.  
Once permuted the order of the mass matrix will be: 
Re\[Phi]1, Im\[Phi]3, Im\[Phi]1, Re\[Phi]3, Re\[Phi]2, Im\[Phi]2 (charged dof)
Re\[Phi]2, Im\[Phi]2, Im\[Phi]1, Re\[Phi]3, Re\[Phi]1, Im\[Phi]3  (neutral dof)*)
scalarPermutationMatrix = {
{1,0,0,0,0,0,0,0,0,0,0,0},
{0,0,0,0,0,0,0,0,0,0,1,0},
{0,0,1,0,0,0,0,0,0,0,0,0},
{0,0,0,0,0,0,0,0,1,0,0,0},
{0,0,0,0,1,0,0,0,0,0,0,0},
{0,0,0,0,0,0,1,0,0,0,0,0},
{0,0,0,0,0,1,0,0,0,0,0,0},
{0,0,0,0,0,0,0,1,0,0,0,0},
{0,0,0,1,0,0,0,0,0,0,0,0},
{0,0,0,0,0,0,0,0,0,1,0,0},
{0,1,0,0,0,0,0,0,0,0,0,0},
{0,0,0,0,0,0,0,0,0,0,0,1}};
If[!OrthogonalMatrixQ[scalarPermutationMatrix], Print["Error, permutation matrix is not orthogonal"]];
exportUTF8[exportPath<>"/ScalarPermutationMatrix.txt", StringReplace[ToString[scalarPermutationMatrix],{"{"->"[","}"->"]"}]];


(*Our casescalarPermutationMatrix is symmetric but taking transpose anyway for consistency/future proofing*)
blockDiagonalMM = Transpose[scalarPermutationMatrix] . scalarMM . scalarPermutationMatrix;

MMblock1 = Take[blockDiagonalMM,{1,6},{1,6}];
MMblock2 = Take[blockDiagonalMM,{7,12},{7,12}];
(* We only handle symmetric mass matrices at the moment 
shouldn't be hard to generalise to hermitian matrices *)
If[!SymmetricMatrixQ[MMblock1] || !SymmetricMatrixQ[MMblock2], Print["Error, block not symmetric!"]];


exportMatrices[exportPath<>"/ScalarMassMatrix.txt", {MMblock1, MMblock2}];


(* ::Subsubsection:: *)
(*Construct scalar rotation matrix *)


(** We cannot diagonalise our mass matrix analytically. So we construct two arbitrary 6x6 matrices to act as our rotation matrices.
These 6x6 matrices are then put into one 12x12 rotation matrix. This minimises the work DRalgo has to do as half the entries of the rotation matrix are zero.
We do also have to apply the permutation matrix that we used to make the mass matrix block diagonal in the first place.
We then fix the value of the rotation matrix numerically in BLOOP and plug them into the effectively potential.
This does mean that symbollicaly our effective potential is not in the mass basis, but it does end up there numerically.
We note here that the model does not violate CP (explicitly or spontaneously) then the mass matrix can be further block diagonalised for further perfomance gains**)

blockSize = 6;
MMblock1Rotation = toIndexedSymbols[ "RUL", {0, 5}, {0, 5}];
MMblock2Rotation = toIndexedSymbols[ "RBR", {0, 5}, {0, 5}];
DSRotBlock = Normal[BlockDiagonalMatrix[{MMblock1Rotation,MMblock2Rotation}]];

(** Make a diagonalMatrix with elements "str<idx>" to represent eigenvalues of mass matrix**)
ScalarMassDiag =Normal[DiagonalMatrix[toIndexedSymbols["MSsq", {0, 11}]]];

(* V = \[Phi]^T.M.\[Phi] 
	 = \[Phi]^T.P.P^T.M.P.P^T.\[Phi] = \[Phi]^T.P.B.P^T.\[Phi], make the mass matrix block diagonal, with some permutation matrix P: P^T.M.P = B
	 = \[Phi]^T.P.S.S^T.B.S.S^T.P^T.\[Phi] = \[Phi]^T.P.S.B.S^T.P^T.\[Phi], make the block diagonal mass matrix diagonal, with some similarity transform S: S^T.B.P = D'
Note P = scalarPermutationMatrix, S = DSRotBlock
Since we give DRalgo an arbitrary diagonal matrix and rotation matrix we have
V = \[Phi]^T.M.\[Phi]
  = \[Phi]^T.R.R^T.M.R.R^T.\[Phi] = \[Phi]^T.R.D.R^T.\[Phi]
We impose D = D' so R = P.S
We compute D' and S in BLOOP numerically
*)

DSRot = scalarPermutationMatrix . DSRotBlock;


exportUTF8[exportPath<>"/ScalarRotationMatrix.json", matrixToJSON[DSRot]];
exportUTF8[exportPath<>"/ScalarMassNames.json", extractSymbols[ScalarMassDiag]];


(* ::Subsection:: *)
(*Gauge field diagonalization*)


(* ::Text:: *)
(*The SM is simple enough to be worth analytically diagonalising *)
(*We currently do not support gauge groups that cannot be diagonalised symbolically. But this could be added if there's demand. *)


VectorMassMatrix = PrintTensorsVEV[2]//Normal;

(** Take the only nontrivial 4x4 submatrix and diagonalize that **) 
{VectorEigenvalues, VectorEigenvectors} = Eigensystem[VectorMassMatrix];
(*This is to match how DRalgo works internally based on SM example*)
(*Tranpose needed as mathematica uses the convention D = SMS^-1 whereas DRalgo and python use the opposite*)
DVRot = Transpose[Simplify[ Normalize /@ VectorEigenvectors, Assumptions -> {g3>0, g2>0, g1>0}]];
VectorEigenvaluesSimp = Simplify[ VectorEigenvalues, Assumptions -> {g3>0, g2>0, g1>0}];


(** Simplify with easier symbols **)
gaugeRotationSubst = {g1/Sqrt[g1^2+g2^2] -> stW, g2/Sqrt[g1^2+g2^2] -> ctW};
vectorShorthands = {stW-> g1/Sqrt[g1^2+g2^2], ctW-> g2/Sqrt[g1^2+g2^2]};
DVRotSimp = DVRot /. gaugeRotationSubst;


(** Easier for DRalgo to handle if we make the mass matrix just single symbols **)
{VectorMassDiagSimple, VectorMassExpressions} = toSymbolicMatrix[DiagonalMatrix[VectorEigenvaluesSimp], mVsq];


exportUTF8[exportPath<>"/VectorMasses.txt", VectorMassExpressions];
exportUTF8[exportPath<>"/VectorShorthands.txt", vectorShorthands];


(* ::Section:: *)
(*Effective potential*)


(** RotateTensorsCustomMass[] is very very slow, this can run for hours!
FastRotate does skips a rotation to make it much faster, made minimal difference to end numerical result (been a while double check) **)
RotateTensorsCustomMass[DSRot,DVRotSimp,ScalarMassDiag,VectorMassDiagSimple, FastRotation-> True];
CalculatePotentialUS[]


(* ::Text:: *)
(*##############       weird behaviour     #################*)
(*For reasons beyond me a SM term in NNLO is different to the SM example.  *)
(*We get (ctW^2*g2^2*Sqrt[mVsq0]*Sqrt[mVsq1])/(12*Pi^2) = g2^5 v^2/(48\[Pi]^2 \[Sqrt]g1^2+g2^2)*)*)
(*In the SM example it is g2^6 v^2/(48\[Pi]^2(g1^2+g2^2)) *)
(*Unsure if bug or I implemented the rotation wrong or its because of BSM physics*)
(*Based on integration tests this has a minor impact on results which is expected since just one term is a factor of ctW off*)
(*I have just been manually changing that term in the NNLO txt file to match the SM case*)


veffLO = PrintEffectivePotential["LO"]//Simplify; (* Simplify needed to get rid of spurious imaginary units *)
veffNLO = PrintEffectivePotential["NLO"]//Simplify;
veffNNLO = PrintEffectivePotential["NNLO"]/.\[Mu]3US->ultraSoftScale; (* not simplified as takes forever and a lot of ram *)


exportUTF8[exportPath<>"/Veff_LO.txt", spiltExpression[veffLO]];
exportUTF8[exportPath<>"/Veff_NLO.txt", spiltExpression[veffNLO]];
exportUTF8[exportPath<>"/Veff_NNLO.txt", spiltExpression[veffNNLO]];


(* I think this is using the \[CapitalLambda]4 at the (ultra)soft scale.
This could lead to problems in the pert check as the soft scale as extra terms from the debye fields*)
exportUTF8[
	exportPath<>"/LagranianSymbols.json", 
	{"fourPointSymbols"-> extractSymbols[\[CapitalLambda]4],
	"threePointSymbols"-> extractSymbols[\[CapitalLambda]3],
	"twoPointSymbols"-> extractSymbols[\[Mu]ij],
	"gaugeSymbols"-> extractSymbols[GaugeCouplings],
	"yukawaSymbols" -> extractSymbols[Ysff],
	"fieldSymbols" -> extractSymbols[backgroundFieldsFull]}
];


exportUTF8[exportPath<>"/AllSymbols.json",
	Sort[DeleteDuplicates[Join[
	extractSymbols[veffLO],
	extractSymbols[veffNLO],
	extractSymbols[veffNNLO],
	extractSymbols[VectorMassExpressions],
	extractSymbols[ScalarMassDiag],
	extractSymbols[MMblock1],
	extractSymbols[MMblock2],
	extractSymbols[ultraSoftParamsRGE],
	extractSymbols[ultrasoftScaleParams],
	extractSymbols[softParamsRGE],
	extractSymbols[hardToSoft],
	extractSymbols[betaFunctions4DUnsquared]
	]]]
];
