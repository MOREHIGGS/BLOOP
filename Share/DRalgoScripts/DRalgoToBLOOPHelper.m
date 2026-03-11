(* ::Package:: *)

(* ::Input:: *)
(*(*************************************************************************)
(*A collection of functions to transform DRalgo output into BLOOP input*)
(*User note: All of these functions are written by LLMs, as I (Jasmine) do not like coding in Mathematica.  *)
(*I have only verfifed they do the things I need them to so I *)
(*apologise if they are unreadable or unoptimal.*)
(*************************************************************************)*)
(**)


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


makeCythonFriendly[expr_] :=
 Module[{str, repeatVar},
  str = ToString[expr, InputForm];
  repeatVar[var_, n_] := StringRiffle[ConstantArray[var, n], "*"];

  StringReplace[str, {
  
  RegularExpression["(\\w+)\\^\\(-(\\d+)/2\\)"] :>
  Module[{v = "$1", n = ToExpression["$2"]},
    "1/csqrt[" <> repeatVar[v, n] <> "]"
  ],

(* x^(-n) \[RightArrow] 1/(x*x*...) *)
RegularExpression["(\\w+)\\^\\(-(\\d+)\\)"] :>
  Module[{v = "$1", n = ToExpression["$2"]},
    "1/(" <> repeatVar[v, n] <> ")"
  ],

    (* x^(n/2) \[RightArrow] csqrt[x*x*...] *)
    RegularExpression["(\\w+)\\^\\((\\d+)/2\\)"] :>
     Module[{v = "$1", n = ToExpression["$2"]},
       "csqrt[" <> repeatVar[v, n] <> "]"
     ],

    (* x^n \[RightArrow] (x*x*...) *)
    RegularExpression["(\\w+)\\^(\\d+)"] :>
     Module[{v = "$1", n = ToExpression["$2"]},
       "(" <> repeatVar[v, n] <> ")"
     ],

    (* integer division \[RightArrow] float division *)
    RegularExpression["\\b(\\d+)/(\\d+)\\b"] :> "$1.0/$2"
  }]
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
