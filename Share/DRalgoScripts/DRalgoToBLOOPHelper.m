(* ::Package:: *)

(* ::Input:: *)
(*(*************************************************************************)
(*A collection of functions to transform DRalgo output into BLOOP input*)
(*Most of the code here is written by LLMs, as non of the devs enjoy coding in Mathematica.  *)
(*************************************************************************)*)
(**)


exportToBLOOP["test.txt", y->x^(3/2)];


exportToBLOOP["test.txt",{x->y^2+\[Pi], y->x^(3/2)}];


exportToBLOOP[fileName_, expr_, complex_: False] := Module[{lines},
    lines = StringRiffle[makeBLOOPFriendly[#, complex] & /@ Flatten[{expr}], "\n"];
    Export[fileName, lines, "Text", CharacterEncoding -> "UTF-8"]
];


(* The regex magic here isn't ideal but every attempt to use expression logic
has been worse
Optional complex argument needed because BLOOP does all but the Veff calculations
with float64 types for speed
Unclear if in Cython x^n gets compiled to x*x*... (TEST) but easy enforce to enforce it
TODO add a check for the size of n as don't want to expand x^(100\[Placeholder])
x^(n/2) -> <c>sqrt(x*x*x) needed as with cdivision on Cython treats x^(3/2) as 0 
*)
makeBLOOPFriendly[expr_, complex_: False] :=
 Module[{str, repeatVar, sqrt, log},
  sqrt = If[complex, "csqrt", "sqrt"];
  log = If[complex, "clog", "log"];
  
  str = ToString[N[expr], InputForm];
  
  repeatVar[var_, n_] := StringRiffle[ConstantArray[var, n], "*"];
  str = StringReplace[str, {
     (* Turn x^(-n/2) into 1/<c>sqrt(x*x*x...)*)
     RegularExpression["(\\w+)\\^\\(-(\\d+)/2\\)"] :>
      ("1/" <> sqrt <> "(" <> repeatVar["$1", ToExpression["$2"]] <> ")"),
     (* Turn x^-n into 1/(x*x*x...)*)
     RegularExpression["(\\w+)\\^\\(-(\\d+)\\)"] :>
      ("1/(" <> repeatVar["$1", ToExpression["$2"]] <> ")"),
     (* Turn x^(n/2) into <c>sqrt(x*x*x...)*)
     RegularExpression["(\\w+)\\^\\((\\d+)/2\\)"] :>
      (sqrt <> "(" <> repeatVar["$1", ToExpression["$2"]] <> ")"),
     (* Turn x^n into (x*x*x...) *)
     RegularExpression["(\\w+)\\^(\\d+)"] :>
      ("(" <> repeatVar["$1", ToExpression["$2"]] <> ")"),
     RegularExpression["\\b(\\d+)/(\\d+)\\b"] :> "$1.0/$2"
     }];
  StringReplace[str, {
    "[" -> "(",
    "]" -> ")",
    "Sqrt" -> sqrt,
    "Log" -> log,
    "^" -> "**"
    }]
 ]


exportUTF8[fileName_, expr_] := Module[{},
  If[StringQ[expr],
    Export[fileName, expr, "Text", CharacterEncoding -> "UTF-8"],
    Export[fileName, expr, CharacterEncoding -> "UTF-8"]
  ]
];


exportMatrices[file_, mats_] :=
  exportUTF8[file, StringRiffle[
    (Module[{n = Length[#]},
       StringRiffle[Flatten @ Table[
         "[" <> ToString[i-1] <> "][" <> ToString[j-1] <> "] -> " <>
           ToString[#[[i,j]], InputForm],
         {i,n},{j,i,n}], "\n"]] &) /@ mats,
    "\n---\n"]]


(* This regex magic is not ideal but every attempt to use something more native to mathematica has been some how less readable with more bugs
The main point of this function is that x^(3/2) isn't handled properly in Cython with cdivision on.
Side points are to do compiler optimisations and handle some of the mathematica syntax
*)
makeCythonFriendly[expr_] :=
 Module[{str, repeatVar},

  str = ToString[expr, InputForm];

  repeatVar[var_, n_] :=
    StringRiffle[ConstantArray[var, n], "*"];

  str = StringReplace[str, {
	 (* Turn x^(-n/2) into 1/csqrt(x*x*x...)*)
     RegularExpression["(\\w+)\\^\\(-(\\d+)/2\\)"] :>
      ("1/csqrt(" <> repeatVar["$1", ToExpression["$2"]] <> ")"),
	(* Turn x^-n into 1/(x*x*x...)*)
     RegularExpression["(\\w+)\\^\\(-(\\d+)\\)"] :>
      ("1/(" <> repeatVar["$1", ToExpression["$2"]] <> ")"),
	(* Turn x^(n/2) into csqrt(x*x*x...)*)
     RegularExpression["(\\w+)\\^\\((\\d+)/2\\)"] :>
      ("csqrt(" <> repeatVar["$1", ToExpression["$2"]] <> ")"),
	(* Turn x^n into x*x*x... *)
     RegularExpression["(\\w+)\\^(\\d+)"] :>
      ("(" <> repeatVar["$1", ToExpression["$2"]] <> ")"),

     RegularExpression["\\b(\\d+)/(\\d+)\\b"] :> "$1.0/$2"
     }];

  StringReplace[str, {
    "[" -> "(",
    "]" -> ")",
    "Sqrt" -> "csqrt",
    "Log" -> "clog",
    "^" -> "**"
    }]
 ]


(* For reasons beyond me the compiler finds it easier to handle lots of small expressions rather than big expressions *)
spiltExpression[expr_] := Module[
  {terms},
  terms = If[Head[expr] === Plus, List @@ expr, {expr}];
  "a += " <> makeCythonFriendly[N[#]] <> ";" & /@ terms
]


solveRunning3D[betaFunction_, newScale_, oldScale_] :=
  betaFunction /. (x_ -> b_) :> (x -> x + b Log[newScale/oldScale])


combineSubstRules[l1_, l2_] :=
  Normal @ Merge[Join[l1, l2], Total]


sqrtSubRules[rules_] :=
  rules /. (x_^2 -> y_) :> (x -> Sqrt[y])


extractSymbols[expr_] :=
 Module[{},
  symExtract[e_] :=
   DeleteDuplicates @ Select[
     Cases[e, _Symbol, Infinity],
     !MemberQ[Attributes[#], Protected] &
   ];

  Which[
   ListQ[expr] && AllTrue[expr, MatchQ[#, _Rule | _RuleDelayed] &],
   SymbolName /@ DeleteDuplicates @ symExtract[Join[expr[[All, 1]], expr[[All, 2]]]],
   Head[expr] === SparseArray,
   SymbolName /@ symExtract[expr["NonzeroValues"]],
   True,
   SymbolName /@ symExtract[expr]
  ]
 ]


removeDRalgoSuffixes[rules_] :=
  Fold[
    (#1 /. s_Symbol /; StringEndsQ[SymbolName[s], #2] :>
      Symbol[StringDrop[SymbolName[s], -StringLength[#2]]]) &,
    rules, {"3dUS", "3d"}]


toSymbolicMatrix[matrix_, base_] :=
 Module[{count = 0, rules = {}, makeSym, sym},

  makeSym[el_] :=
   If[NumericQ[el],
    el,
    sym = Symbol[SymbolName[base] <> ToString[count++]];
    rules = Append[rules, sym -> el];
    sym
   ];

  {Map[makeSym, matrix, {2}], rules}
 ]


matrixToJSON[mat_] :=
 ExportString[
  Association @ Map[
    ToString[#] -> (First@Position[mat, #] - 1) &,
    DeleteDuplicates @ Cases[mat, _Symbol, Infinity]
  ],
  "JSON"
 ]


toIndexedSymbols[symbol_, ranges__] :=
 Module[{r = List@ranges, base},

  base = If[StringQ[symbol], symbol, SymbolName[symbol]];

  Array[
   Symbol[
     base <> StringJoin[ToString /@ Flatten[{##}]]
   ] &,
   r[[All, 2]] - r[[All, 1]] + 1,
   r[[All, 1]]
  ]
 ]
