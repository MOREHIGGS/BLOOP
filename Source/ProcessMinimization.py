import numpy as np

def interpretData(result, bmNumber, bmInput, fieldNames):
    processedResult = {
        "bmNumber": bmNumber,
        "bmInput": bmInput,
        "failureReason": result["failureReason"],
        "fieldJumps": None,
        "strong": False,
        "steps": 0
    }

    if result["failureReason"]:
        return processedResult 

    processedResult |= {"isPerturbative": bool(np.all(result["bIsPerturbative"])),
                        "complex": bool(np.any(
                                 np.abs( np.array(result["vevDepthImag"]) / np.array(result["vevDepthReal"])
                                        ) > 1e-8
                                        ))
                        }
      

    allFieldValues = result["vevLocation"] / np.sqrt(result["T"])
    allFieldValuesD = np.diff(allFieldValues)
    allFieldValuesT = allFieldValues.transpose() 
    
    fieldLengthDiff = np.array([ np.linalg.norm(allFieldValuesT[idx]) 
                       - np.linalg.norm(allFieldValuesT[idx+1]) 
                       for idx in range(len(allFieldValuesT)-1) ])  
    
    PTIndices = (fieldLengthDiff > 0.6).nonzero()
    if len(PTIndices) > 0:
        processedResult["steps"] = len(fieldLengthDiff[PTIndices])
        processedResult["strong"] = float(max(fieldLengthDiff[PTIndices]))
        results = []
        
        for idx in PTIndices:
            resultDic = {}
            for fieldNameIdx, fieldJumps in enumerate(allFieldValuesD):
                if abs(fieldJumps[idx]) > 0.1:
                    resultDic[fieldNames[fieldNameIdx]] = float(fieldJumps[idx])
            results.append(resultDic)
        
        processedResult["fieldJumps"] = results

    return processedResult
