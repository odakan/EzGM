"""
Ground motion record processing ToolBox
"""

import numpy as np
import numpy.matlib
from scipy.integrate import cumtrapz
from scipy.fft import fft, fftfreq, fftshift
from scipy.signal import butter, filtfilt

def baseline_correction(values, dt, polynomial_type):
    """
    Details
    -------
    This script will return baseline corrected values for the given signal
    
    Notes
    -----
    Applicable for Constant, Linear, Quadratic and Cubic polynomial functions
        
    References
    ----------
    Kramer, Steven L. 1996. Geotechnical Earthquake Engineering. Prentice Hall
        
    Parameters
    ----------
    values: numpy.array
        signal values      
    dt: float          
        sampling interval
    polynomial_type: str
        type of baseline correction 'Constant', 'Linear', 'Quadratic', 'Cubic'    
        
    Returns
    -------
    values_corrected: numpy.array
        corrected values
        
    """

    if polynomial_type == 'Constant':
        n = 0
    elif polynomial_type == 'Linear':
        n = 1
    elif polynomial_type == 'Quadratic':
        n = 2
    elif polynomial_type == 'Cubic':
        n = 3

    t = np.linspace(0, (len(values) - 1) * dt, len(values))  # Time array
    P = np.polyfit(t, values, n)  # Best fit line of values
    po_va = np.polyval(P, t)  # Matrix of best fit line
    values_corrected = values - po_va  # Baseline corrected values

    return values_corrected


def butterworth_filter(values, dt, cut_off=(0.1, 25), **kwargs):
    """
    Details
    -------
    This script will return filtered values for the given signal
    
    References
    ----------
    Kramer, Steven L. 1996. Geotechnical Earthquake Engineering, Prentice Hall
        
    Parameters
    ----------
    values: numpy.array
        Input signal
    dt: float
        time-step
    cut_off: tuple, list, optional          
        Lower and upper cut off frequencies for the filter, if None then no filter. 
        e.g. (None, 15) applies a lowpass filter at 15Hz, whereas (0.1, 10) applies
        a bandpass filter at 0.1Hz to 10Hz.
    kwargs: keyword arguments, optional
        filter_order: int
            Order of the Butterworth filter (default = 4)
        remove_gibbs: str, the default is None.
            Pads with zeros to remove the Gibbs filter effect
            if = 'start' then pads at start,
            if = 'end' then pads at end,
            if = 'mid' then pads half at start and half at end
        gibbs_extra: int, the default is 1
            Each increment of the value doubles the record length using zero padding.
        gibbs_range: int, the default is 50
            gibbs index range
    Returns
    -------
    values_filtered: numpy.array
        Filtered signal
    """

    if isinstance(cut_off, list) or isinstance(cut_off, tuple):
        pass
    else:
        raise ValueError("cut_off must be list or tuple.")
    if len(cut_off) != 2:
        raise ValueError("cut_off must be length 2.")
    if cut_off[0] is not None and cut_off[1] is not None:
        filter_type = "band"
        cut_off = np.array(cut_off)
    elif cut_off[0] is None:
        filter_type = 'low'
        cut_off = cut_off[1]
    else:
        filter_type = 'high'
        cut_off = cut_off[0]

    filter_order = kwargs.get('filter_order', 4)
    remove_gibbs = kwargs.get('remove_gibbs', None)
    gibbs_extra = kwargs.get('gibbs_extra', 1)
    gibbs_range = kwargs.get('gibbs_range', 50)
    sampling_rate = 1.0 / dt
    nyq = sampling_rate * 0.5

    values_filtered = values
    org_len = len(values_filtered)

    if remove_gibbs is not None:
        # Pad end of record with extra zeros then cut it off after filtering
        nindex = int(np.ceil(np.log2(len(values_filtered)))) + gibbs_extra
        new_len = 2 ** nindex
        diff_len = new_len - org_len
        if remove_gibbs == 'start':
            s_len = 0
            f_len = s_len + org_len
        elif remove_gibbs == 'end':
            s_len = diff_len
            f_len = s_len + org_len
        else:
            s_len = int(diff_len / 2)
            f_len = s_len + org_len

        end_value = np.mean(values_filtered[-gibbs_range:])
        start_value = np.mean(values_filtered[:gibbs_range])
        temp = start_value * np.ones(new_len)
        temp[f_len:] = end_value
        temp[s_len:f_len] = values_filtered
        values_filtered = temp
    else:
        s_len = 0
        f_len = org_len

    wp = cut_off / nyq
    b, a = butter(filter_order, wp, btype=filter_type)
    values_filtered = filtfilt(b, a, values_filtered)
    # removing extra zeros from gibbs effect
    values_filtered = values_filtered[s_len:f_len]

    return values_filtered


def sdof_ltha(Ag, dt, T, xi, m):
    """
    Details
    -------
    This script will carry out linear time history analysis for SDOF system
    It currently uses Newmark Beta Method
    
    References
    ---------- 
    Chopra, A.K. 2012. Dynamics of Structures: Theory and 
    Applications to Earthquake Engineering, Prentice Hall.
    N. M. Newmark, “A Method of Computation for Structural Dynamics,”
    ASCE Journal of the Engineering Mechanics Division, Vol. 85, 1959, pp. 67-94.
    
    Notes
    -----
    * Linear Acceleration Method: Gamma = 1/2, Beta = 1/6
    * Average Acceleration Method: Gamma = 1/2, Beta = 1/4
    * Average acceleration method is unconditionally stable,
      whereas linear acceleration method is stable only if dt/Tn <= 0.55
      Linear acceleration method is preferable due to its accuracy.
    
    Parameters
    ----------
    Ag: numpy.array    
        Acceleration values
    dt: float
        Time step [sec]
    T:  float, numpy.array
        Considered period array e.g. 0 sec, 0.1 sec ... 4 sec
    xi: float
        Damping ratio, e.g. 0.05 for 5%
    m:  float
        Mass of SDOF system
        
    Returns
    -------
    u: numpy.array       
        Relative displacement response history
    v: numpy.array   
        Relative velocity response history
    ac: numpy.array 
        Relative acceleration response history
    ac_tot: numpy.array 
        Total acceleration response history
    """

    # Get the length of acceleration history array
    n1 = max(Ag.shape)
    # Get the length of period array
    n2 = max(T.shape)
    T = T.reshape((1, n2))

    # Assign the external force
    p = -m * Ag

    # Calculate system properties which depend on period
    fn = 1 / T  # frequency
    wn = 2 * np.pi * fn  # circular natural frequency
    k = m * wn ** 2  # actual stiffness
    c = 2 * m * wn * xi  # actual damping coefficient

    # Newmark Beta Method coefficients
    Gamma = np.ones((1, n2)) * (1 / 2)
    # Use linear acceleration method for dt/T<=0.55
    Beta = np.ones((1, n2)) * 1 / 6
    # Use average acceleration method for dt/T>0.55
    Beta[np.where(dt / T > 0.55)] = 1 / 4

    # Compute the constants used in Newmark's integration
    a1 = Gamma / (Beta * dt)
    a2 = 1 / (Beta * dt ** 2)
    a3 = 1 / (Beta * dt)
    a4 = Gamma / Beta
    a5 = 1 / (2 * Beta)
    a6 = (Gamma / (2 * Beta) - 1) * dt
    kf = k + a1 * c + a2 * m
    a = a3 * m + a4 * c
    b = a5 * m + a6 * c

    # Initialize the history arrays
    u = np.zeros((n1, n2))  # relative displacement history
    v = np.zeros((n1, n2))  # relative velocity history
    ac = np.zeros((n1, n2))  # relative acceleration history
    ac_tot = np.zeros((n1, n2))  # total acceleration history

    # Set the Initial Conditions
    u[0] = 0
    v[0] = 0
    ac[0] = (p[0] - c * v[0] - k * u[0]) / m
    ac_tot[0] = ac[0] + Ag[0]

    for i in range(n1 - 1):
        dpf = (p[i + 1] - p[i]) + a * v[i] + b * ac[i]
        du = dpf / kf
        dv = a1 * du - a4 * v[i] - a6 * ac[i]
        da = a2 * du - a3 * v[i] - a5 * ac[i]

        # Update history variables
        u[i + 1] = u[i] + du
        v[i + 1] = v[i] + dv
        ac[i + 1] = ac[i] + da
        ac_tot[i + 1] = ac[i + 1] + Ag[i + 1]

    return u, v, ac, ac_tot


def get_parameters(self, Ag, dt, T, xi):
    """
    Details
    -------
    This script will return various ground motion parameters for a given record
        
    References
    ---------- 
    Kramer, Steven L. 1996. Geotechnical Earthquake Engineering, Prentice Hall
    Chopra, A.K. 2012. Dynamics of Structures: Theory and 
    Applications to Earthquake Engineering, Prentice Hall.
        
    Parameters
    ----------
    Ag: numpy.array    
        Acceleration values [m/s2]
    dt: float
        Time step [sec]
    T:  float, numpy.array
        Considered period array e.g. 0 sec, 0.1 sec ... 4 sec
    xi: float
        Damping ratio, e.g. 0.05 for 5%
        
    Returns
    -------
    param: dictionary
        Contains the following intensity measures:
    PSa(T): numpy.array       
        Elastic pseudo-acceleration response spectrum [m/s2]
    PSv(T): numpy.array   
        Elastic pseudo-velocity response spectrum [m/s]
    Sd(T): numpy.array 
        Elastic displacement response spectrum  - relative displacement [m]
    Sv(T): numpy.array 
        Elastic velocity response spectrum - relative velocity at [m/s]
    Sa(T): numpy.array 
        Elastic accleration response spectrum - total accelaration [m/s2]
    Ei_r(T): numpy.array 
        Relative input energy spectrum for elastic system [N.m]
    Ei_a(T): numpy.array 
        Absolute input energy spectrum for elastic system [N.m]
    Periods: numpy.array 
        Periods where spectral values are calculated [sec]
    FAS: numpy.array 
        Fourier amplitude spectra
    PAS: numpy.array 
        Power amplitude spectra
    PGA: float
        Peak ground acceleration [m/s2]
    PGV: float
        Peak ground velocity [m/s]
    PGD: float
        Peak ground displacement [m]
    Aint: numpy.array 
        Arias intensity ratio vector with time [m/s]
    Arias: float 
        Maximum value of arias intensity ratio [m/s]
    HI: float
        Housner intensity ratio [m]
        Requires T to be defined between (0.1-2.5 sec)
        Otherwise not applicable, and equal to 'N.A'
    CAV: float
        Cumulative absolute velocity [m/s]        
    t_5_75: list
        Significant duration time vector between 5% and 75% of energy release (from Aint)
    D_5_75: float
        Significant duration between 5% and 75% of energy release (from Aint)
    t_5_95: list    
        Significant duration time vector between 5% and 95% of energy release (from Aint)
    D_5_95: float
        Significant duration between 5% and 95% of energy release (from Aint)
    t_bracketed: list 
        Bracketed duration time vector (acc>0.05g)
        Not applicable, in case of low intensity records, 
        Thus, equal to 'N.A'
    D_bracketed: float
        Bracketed duration (acc>0.05g)
        Not applicable, in case of low intensity records, 
        Thus, equal to 'N.A'
    t_uniform: list 
        Uniform duration time vector (acc>0.05g)
        Not applicable, in case of low intensity records, 
        Thus, equal to 'N.A'
    D_uniform: float 
        Uniform duration (acc>0.05g)
        Not applicable, in case of low intensity records, 
        Thus, equal to 'N.A'
    Tm: float
        Mean period
    Tp: float             
        Predominant Period
    aRMS: float 
        Root mean square root of acceleration [m/s2]
    vRMS: float
        Root mean square root of velocity [m/s]
    dRMS: float  
        Root mean square root of displacement [m]
    Ic: float     
        End time might which is used herein, is not always a good choice
    ASI: float   
        Acceleration spectrum intensity [m/s]
        Requires T to be defined between (0.1-0.5 sec)
        Otherwise not applicable, and equal to 'N.A'
    MASI: float [m]
        Modified acceleration spectrum intensity
        Requires T to be defined between (0.1-2.5 sec)
        Otherwise not applicable, and equal to 'N.A'
    VSI: float [m]
        Velocity spectrum intensity
        Requires T to be defined between (0.1-2.5 sec)
        Otherwise not applicable, and equal to 'N.A'
    """

    # INITIALIZATION
    T = T[T != 0]  # do not use T = zero for response spectrum calculations
    param = {'Periods': T}

    # GET SPECTRAL VALUES
    # Get the length of acceleration history array
    n1 = max(Ag.shape)
    # Get the length of period array
    n2 = max(T.shape)
    # Create the time array
    t = np.linspace(0, (n1 - 1) * dt, n1)
    # Get ground velocity and displacement through integration
    Vg = cumtrapz(Ag, t, initial=0)
    Dg = cumtrapz(Vg, t, initial=0)
    # Mass (kg)
    m = 1
    # Carry out linear time history analyses for SDOF system
    u, v, ac, ac_tot = self.sdof_ltha(Ag, dt, T, xi, m)
    # Calculate the spectral values
    param['Sd'] = np.max(np.abs(u), axis=0)
    param['Sv'] = np.max(np.abs(v), axis=0)
    param['Sa'] = np.max(np.abs(ac_tot), axis=0)
    param['PSv'] = (2 * np.pi / T) * param['Sd']
    param['PSa'] = ((2 * np.pi / T) ** 2) * param['Sd']
    ei_r = cumtrapz(-numpy.matlib.repmat(Ag, n2, 1).T, u, axis=0, initial=0) * m
    ei_a = cumtrapz(-numpy.matlib.repmat(Dg, n2, 1).T, ac_tot, axis=0, initial=0) * m
    param['Ei_r'] = ei_r[-1]
    param['Ei_a'] = ei_a[-1]

    # GET PEAK GROUND ACCELERATION, VELOCITY AND DISPLACEMENT
    param['PGA'] = np.max(np.abs(Ag))
    param['PGV'] = np.max(np.abs(Vg))
    param['PGD'] = np.max(np.abs(Dg))

    # GET ARIAS INTENSITY
    Aint = np.cumsum(Ag ** 2) * np.pi * dt / (2 * 9.81)
    param['Arias'] = Aint[-1]
    temp = np.zeros((len(Aint), 2))
    temp[:, 0] = t
    temp[:, 1] = Aint
    param['Aint'] = temp

    # GET HOUSNER INTENSITY
    try:
        index1 = np.where(T == 0.1)[0][0]
        index2 = np.where(T == 2.5)[0][0]
        param['HI'] = np.trapz(param['PSv'][index1:index2], T[index1:index2])
    except:
        param['HI'] = 'N.A.'

    # SIGNIFICANT DURATION (5%-75% Ia)
    mask = (Aint >= 0.05 * Aint[-1]) * (Aint <= 0.75 * Aint[-1])
    timed = t[mask]
    t1 = round(timed[0], 3)
    t2 = round(timed[-1], 3)
    param['t_5_75'] = [t1, t2]
    param['D_5_75'] = round(t2 - t1, 3)

    # SIGNIFICANT DURATION (5%-95% Ia)
    mask = (Aint >= 0.05 * Aint[-1]) * (Aint <= 0.95 * Aint[-1])
    timed = t[mask]
    t1 = round(timed[0], 3)
    t2 = round(timed[-1], 3)
    param['t_5_95'] = [t1, t2]
    param['D_5_95'] = round(t2 - t1, 3)

    # BRACKETED DURATION (0.05g)
    try:
        mask = np.abs(Ag) >= 0.05 * 9.81
        # mask = np.abs(Ag) >= 0.05 * np.max(np.abs(Ag))
        indices = np.where(mask)[0]
        t1 = round(t[indices[0]], 3)
        t2 = round(t[indices[-1]], 3)
        param['t_bracketed'] = [t1, t2]
        param['D_bracketed'] = round(t2 - t1, 3)
    except:  # in case of ground motions with low intensities
        param['t_bracketed'] = 'N.A.'
        param['D_bracketed'] = 'N.A.'

    # UNIFORM DURATION (0.05g)
    try:
        mask = np.abs(Ag) >= 0.05 * 9.81
        # mask = np.abs(Ag) >= 0.05 * np.max(np.abs(Ag))
        indices = np.where(mask)[0]
        t_treshold = t[indices]
        param['t_uniform'] = [t_treshold]
        temp = np.round(np.diff(t_treshold), 8)
        param['D_uniform'] = round(np.sum(temp[temp == dt]), 3)
    except:  # in case of ground motions with low intensities
        param['t_uniform'] = 'N.A.'
        param['D_uniform'] = 'N.A.'

    # CUMULATVE ABSOLUTE VELOCITY
    param['CAV'] = np.trapz(np.abs(Ag), t)

    # CHARACTERISTIC INTENSITY, ROOT MEAN SQUARE OF ACC, VEL, DISP
    Td = t[-1]  # note this might not be the best indicative, different Td might be chosen
    param['aRMS'] = np.sqrt(np.trapz(Ag ** 2, t) / Td)
    param['vRMS'] = np.sqrt(np.trapz(Vg ** 2, t) / Td)
    param['dRMS'] = np.sqrt(np.trapz(Dg ** 2, t) / Td)
    param['Ic'] = param['aRMS'] ** 1.5 * np.sqrt(Td)

    # ACCELERATION AND VELOCITY SPECTRUM INTENSITY
    try:
        index3 = np.where(T == 0.5)[0][0]
        param['ASI'] = np.trapz(param['Sa'][index1:index3], T[index1:index3])
    except:
        param['ASI'] = 'N.A.'
    try:
        param['MASI'] = np.trapz(param['Sa'][index1:index2], T[index1:index2])
        param['VSI'] = np.trapz(param['Sv'][index1:index2], T[index1:index2])
    except:
        param['MASI'] = 'N.A.'
        param['VSI'] = 'N.A.'

    # GET FOURIER AMPLITUDE AND POWER AMPLITUDE SPECTRUM
    # Number of sample points, add zeropads
    N = 2 ** int(np.ceil(np.log2(len(Ag))))
    Famp = fft(Ag, N)
    Famp = np.abs(fftshift(Famp)) * dt
    freq = fftfreq(N, dt)
    freq = fftshift(freq)
    Famp = Famp[freq > 0]
    freq = freq[freq > 0]
    Pamp = Famp ** 2 / (np.pi * t[-1] * param['aRMS'] ** 2)
    FAS = np.zeros((len(Famp), 2))
    FAS[:, 0] = freq
    FAS[:, 1] = Famp
    PAS = np.zeros((len(Famp), 2))
    PAS[:, 0] = freq
    PAS[:, 1] = Pamp
    param['FAS'] = FAS
    param['PAS'] = FAS

    # MEAN PERIOD
    mask = (freq > 0.25) * (freq < 20)
    indices = np.where(mask)[0]
    fi = freq[indices]
    Ci = Famp[indices]
    param['Tm'] = np.sum(Ci ** 2 / fi) / np.sum(Ci ** 2)

    # PREDOMINANT PERIOD
    mask = param['Sa'] == max(param['Sa'])
    indices = np.where(mask)[0]
    param['Tp'] = T[indices]

    return param


def RotDxx_spectrum(self, Ag1, Ag2, dt, T, xi, xx):
    """
    Details
    -------
    This script will return RotDxx spectrum
    It currently uses Newmark Beta Method
    
    References
    ---------- 
    Boore, D. M. (2006). Orientation-Independent Measures of Ground Motion. 
    Bulletin of the Seismological Society of America, 96(4A), 1502–1511.
    Boore, D. M. (2010). Orientation-Independent, Nongeometric-Mean Measures 
    of Seismic Intensity from Two Horizontal Components of Motion. 
    Bulletin of the Seismological Society of America, 100(4), 1830–1835.
    
    Notes
    -----
    * Linear Acceleration Method: Gamma = 1/2, Beta = 1/6
    * Average Acceleration Method: Gamma = 1/2, Beta = 1/4
    * Average acceleration method is unconditionally stable,
      whereas linear acceleration method is stable only if dt/Tn <= 0.55
      Linear acceleration method is preferable due to its accuracy.
        
    Parameters
    ----------
    Ag1 : numpy.array    
        Acceleration values of 1st horizontal ground motion component
    Ag2 : numpy.array    
        Acceleration values of 2nd horizontal ground motion component
    dt: float
        Time step [sec]
    T:  float, numpy.array
        Considered period array e.g. 0 sec, 0.1 sec ... 4 sec
    xi: float
        Damping ratio, e.g. 0.05 for 5%
    xx: int
        Percentile to calculate, e.g. 50 for RotD50
        
    Returns
    -------
    Sa_RotDxx: numpy.array 
        RotDxx Spectra
    """

    # Verify if the length of arrays are the same
    if len(Ag1) == len(Ag2):
        pass
    elif len(Ag1) > len(Ag2):
        Ag2 = np.append(Ag2, np.zeros(len(Ag1) - len(Ag2)))
    elif len(Ag2) > len(Ag1):
        Ag1 = np.append(Ag1, np.zeros(len(Ag2) - len(Ag1)))

    # Get the length of period array 
    n2 = max(T.shape)

    # Mass (kg)
    m = 1

    # Carry out linear time history analyses for SDOF system
    u1, _, _, _ = sdof_ltha(Ag1, dt, T, xi, m)
    u2, _, _, _ = sdof_ltha(Ag2, dt, T, xi, m)

    # RotD definition is taken from Boore 2010.
    Rot_Disp = np.zeros((180, n2))
    for theta in range(0, 180, 1):
        Rot_Disp[theta] = np.max(np.abs(u1 * np.cos(np.deg2rad(theta)) + u2 * np.sin(np.deg2rad(theta))), axis=0)

    Rot_Acc = Rot_Disp * (2 * np.pi / T) ** 2
    Sa_RotDxx = np.percentile(Rot_Acc, xx, axis=0)

    return Sa_RotDxx
