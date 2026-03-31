(* ::Package:: *)

(* ::Input:: *)
(*(*************************************************************************)
(*A collection of functions to transform DRalgo output into BLOOP input*)
(*Most of the code here is written by LLMs, as non of the devs enjoy coding in Mathematica.  *)
(*************************************************************************)*)
(**)


Options[exportToBLOOP] = {"complex" -> False, "raw" -> False};

exportToBLOOP[fileName_, expr_, opts : OptionsPattern[]] := 
 Module[{complexQ, raw, format},
  complexQ = OptionValue["complex"];
  raw = OptionValue["raw"];
  lines = If[
    raw,
    expr,
    StringRiffle[makeBLOOPFriendly[#, complex->complexQ] & /@ Flatten[{expr}], "\n"]
  ];
  format = If[StringEndsQ[fileName, ".json"], "JSON", "Text"];
  Export[fileName, lines, format, CharacterEncoding -> "UTF-8"]
]


(* To ultize the stack/avoid python overhead its better if we write matrices as 
double matrix[n][n]
matrix[i][j] = <expression at position i,j> 
See makeBLOOPFriendly as to why : and ; are used instead of [ and ][
add --- to delimite a new matrix (easier than tracking when i resets back to 0)
*)
(* onlyUpper should only be used for matrices that will be diagonalised *)
Options[exportMatrices] = {"onlyUpper" -> False};
exportMatrices[file_, mats_, opts : OptionsPattern[]] :=
 Module[{upperQ},
  
  upperQ = OptionValue["onlyUpper"];
  
  exportToBLOOP[
   file,
   StringRiffle[
    (Module[{n = Length[#]},
        StringRiffle[
         Flatten@Table[
           ":" <> ToString[i - 1] <> ";:" <> ToString[j - 1] <> "; -> " <>
             ToString[N[#[[i, j]]], InputForm],
           {i, 1, n}, {j, If[upperQ, i, 1], n}
         ],
         "\n"
        ]
      ] &) /@ mats,
    "\n---\n"
   ]
  ]
 ]


(* The regex magic here isn't ideal but every attempt to use expression logic has been worse
Optional complex argument needed because BLOOP does all but the Veff calculations with float64 types for speed
Unclear if in Cython x^n gets compiled to x*x*... but easy enforce to enforce it
TODO add a check for the size of n as don't want to expand x^100 (I don't see why something like this would be in a DRalgo output though)
x^(n/2) -> <c>sqrt(x*x*x) needed as with cdivision on Cython treats x^(3/2) as 0 
*)
Options[makeBLOOPFriendly] = {"complex" -> False};
makeBLOOPFriendly[expr_,opts : OptionsPattern[]] :=
 Module[{str, repeatVar, sqrt, log, complexQ},
 
  complexQ = OptionValue["complex"];
  
  sqrt = If[complexQ, "csqrt", "sqrt"];
  log = If[complexQ, "clog", "log"];
  
  str = If[StringQ[expr], expr, ToString[N[expr], InputForm]];
  
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
     (* Problem [] is a function call in mathematica but an index in C/Python 
     so we need to swap [] for () for function calls, but when we want the index of a matrix we don't want to do that swap
     so whenever we create an expression for a matrix use : and ; as place holders for [] (:; shouldn't ever appear in a DRalgo output so should be safe)
     swap [] for () then swap :; for []
     *);
  StringReplace[str, {
    "[" -> "(",
    "]" -> ")",
    ":" -> "[",
    ";" -> "]",
    "Sqrt" -> sqrt,
    "Log" -> log,
    "^" -> "**",
    "||"-> " or ",
    "&&"-> " and "
    }]
 ]


(* For reasons beyond me the compiler finds it easier to handle lots of small expressions rather than big expressions *)
optimiseVeff[expr_] := Module[
  {terms},
  terms = If[Head[expr] === Plus, List @@ expr, {expr}];
  ToString[N[#], InputForm] & /@ terms
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
