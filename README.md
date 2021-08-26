# EzGM
Toolbox for ground motion record selection and processing. Examples can be found here: https://github.com/volkanozsarac/EzGM/tree/master/Examples

```
pip install EzGM
import EzGM
```
***

- EzGM.Selection.conditional_spectrum is used to perform record selection based on CS(AvgSa) and CS(Sa) for the given metadata. The tool makes use of Openquake hazardlib, thus any available gmpe available can directly be used.
- If user desires to get formatted records, for the given metadata, s/he should place the available records from metadata file into the Records.zip with the name of database.
e.g. EXSIM for metadata EXSIM.mat. In case of NGA_W2, user can also download the records directly by inserting account username and password into the associated method. 

- See https://docs.openquake.org/oq-engine/master/openquake.hazardlib.gsim.html for available ground motion prediction equations.

Example 1, IM = Sa(Tstar) 
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/volkanozsarac/EzGM/master?filepath=%2FExamples%2Fbinder%2FExample1.ipynb)
```
Example1 --> IM = Sa(Tstar)
Example2 --> IM = AvgSa(Tstar)
```
***

- EzGM.Selection.tbdy_2018 is used to perform TBDY 2018 (Turkish Building Code) based record selection
```
Example3
```
***

- EzGM.Selection.ec8_part1 is used to perform Eurocode 8 part 1 based record selection
```
Example4
```
***

- EzGM.OQProc can be used along with EzGM.Selection.conditional_spectrum to perform conditional spectrum (CS) Based Record Selection for multiple stripes analysis
upon carrying out probabilistic seismic hazard analysis (PSHA) via OpenQuake.Engine.
```
Example5
```
***

- EzGM.GMProc can be used to process ground motion records (filtering, baseline corrections, IM calculations).
```
Example6
```

## Note
- ngaw2_download method can be used only if google-chrome is readily available. EzGM is set to download chromedriver automatically into site-packages if it is not available.
- Installation of Openquake package in Linux and MACOS is straightforward. In case of windows the package may not be installed correctly if anaconda is used, in other words, geos_c.dll or similar .dll files could be mislocated). To fix this simply, write:
```
conda install shapely
```

## Acknowledgements
- Special thanks to Besim Yukselen for his help in the development of ngaw2_download method, and Gerard J. O'Reilly for sharing his knowledge in the field with me. The EzGM.conditional_spectrum method is greatly inspired by the CS_Selection code of Prof. Jack W. Baker whom I thank for sharing his work with the research community.
***

## Reference
- If you are going to use the code presented herein for any official study, please refer to 
Ozsarac V, Monteiro R.C., Calvi, G.M. (2021). Probabilistic seismic assessment of RC bridges using simulated records. Structure and Infrastructure Engineering.
***
