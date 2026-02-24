
import numpy as np
from numba import njit


@njit(cache=True)
def Levenshtein_distance(arr_str_1:np.ndarray, arr_str_2:np.ndarray
                         ) -> float:
    """
    Levenshtein distance function.

    Parameters
    ----------
    arr_str_1 : np.ndarray
        First array of the cleaned string from space and dot.
    arr_str_2 : np.ndarray
        Second array of the cleaned string from space and dot.

    Returns
    -------
    float
        Levenshtein distance.

    """
    len1, len2 = len(arr_str_1), len(arr_str_2)
    if len1 < len2:
        return Levenshtein_distance(arr_str_2, arr_str_1)

    prev_row = np.arange(len2+1).astype(np.float64)
    curr_row = np.zeros(len2+1, dtype=np.float64)
    for i in range(1, len1+1):
        curr_row[0] = i
        for j in range(1, len2+1):
            cost = 0.0 if arr_str_1[i-1] == arr_str_2[j-1] else 1.0
            curr_row[j] = min(curr_row[j-1]+1, prev_row[j]+1,
                              prev_row[j-1]+cost)

        prev_row[:] = curr_row[:]

    return prev_row[len2]/max(len1, len2)

@njit(cache=True)
def Levenshtein_distance_es(arr_str_1:np.ndarray, arr_str_2:np.ndarray,
                            treshold:float) -> float:
    """
    Levenshtein distance function with treshold based early stoping.

    Parameters
    ----------
    arr_str_1 : np.ndarray
        First array of the cleaned string from space and dot.
    arr_str_2 : np.ndarray
        Second array of the cleaned string from space and dot.

    Returns
    -------
    float
        Levenshtein distance with 1.0 when early stoping is triggered.

    """
    len1, len2 = len(arr_str_1), len(arr_str_2)
    max_len = max(len1, len2)
    max_dist = treshold*max_len
    if len1 < len2:
        return Levenshtein_distance_es(arr_str_2, arr_str_1, treshold)

    prev_row = np.arange(len2+1).astype(np.float64)
    curr_row = np.zeros(len2+1, dtype=np.float64)
    for i in range(1, len1+1):
        curr_row[0] = i
        for j in range(1, len2 + 1):
            cost = 0.0 if arr_str_1[i-1] == arr_str_2[j-1] else 1.0
            curr_row[j] = min(curr_row[j-1]+1, prev_row[j]+1,
                              prev_row[j-1]+cost)

        if min(curr_row) > max_dist:
            return 1.0

        prev_row[:] = curr_row[:]

    final_dist = prev_row[len2]
    return final_dist/max_len

@njit(cache=True)
def Damerau_Levenshtein_distance(arr_str_1:np.ndarray, arr_str_2:np.ndarray
                                 ) -> float:
    """
    Damerau-Levenshtein distance function.

    Parameters
    ----------
    arr_str_1 : np.ndarray
        First cleaned string from space and dot.
    arr_str_2 : np.ndarray
        Secind cleaned string from space and dot.

    Returns
    -------
    float
        Damerau-Levenshtein distance.

    """
    len1, len2 = len(arr_str_1), len(arr_str_2)
    if len1 < len2:
        return Damerau_Levenshtein_distance(arr_str_2, arr_str_1)

    prev_row = np.arange(0., len2+1., 1., dtype=np.float64)
    prev_m2_row = np.zeros(len2+1, dtype=np.float64)
    curr_row = np.zeros(len2+1, dtype=np.float64)
    for i in range(1, len1+1):
        curr_row[0] = i
        for j in range(1, len2+1):
            # Cost of substitution
            cost = 0.0 if arr_str_1[i-1] == arr_str_2[j-1] else 1.0
            curr_row[j] = min(curr_row[j-1]+1, prev_row[j]+1,
                              prev_row[j-1]+cost)

            if (i > 1) and (j > 1) and (arr_str_1[i-1] == arr_str_2[j-2]) and (
                arr_str_1[i-2] == arr_str_2[j-1]):
                curr_row[j] = min(curr_row[j], prev_m2_row[j-2]+cost)

        prev_m2_row[:] = prev_row[:]
        prev_row[:] = curr_row[:]

    return prev_row[len2]/max(len1, len2)

@njit(cache=True)
def Damerau_Levenshtein_distance_es(arr_str_1:np.ndarray,
                                    arr_str_2:np.ndarray,
                                    treshold:float) -> float:
    """
    Damerau-Levenshtein distance function with treshold based early stoping.

    Parameters
    ----------
    arr_str_1 : np.ndarray
        First cleaned string from space and dot.
    arr_str_2 : np.ndarray
        Secind cleaned string from space and dot.

    Returns
    -------
    float
        Damerau-Levenshtein distance.

    """
    len1, len2 = len(arr_str_1), len(arr_str_2)
    if len1 < len2:
        return Damerau_Levenshtein_distance_es(arr_str_2, arr_str_1, treshold)

    max_len = max(len1, len2)
    max_dist = treshold*max_len
    prev_row = np.arange(0., len2+1., 1., dtype=np.float64)
    prev_m2_row = np.zeros(len2+1, dtype=np.float64)
    curr_row = np.zeros(len2+1, dtype=np.float64)
    for i in range(1, len1+1):
        curr_row[0] = i
        for j in range(1, len2+1):
            # Cost of substitution
            cost = 0.0 if arr_str_1[i-1] == arr_str_2[j-1] else 1.0
            curr_row[j] = min(curr_row[j-1]+1, prev_row[j]+1,
                              prev_row[j-1]+cost)

            if (i > 1) and (j > 1) and (arr_str_1[i-1] == arr_str_2[j-2]) and (
                arr_str_1[i-2] == arr_str_2[j-1]):
                curr_row[j] = min(curr_row[j], prev_m2_row[j-2]+1)

        if (min(curr_row)-1) > max_dist:
            return 1.0

        prev_m2_row[:] = prev_row[:]
        prev_row[:] = curr_row[:]

    return prev_row[len2]/max(len1, len2)
