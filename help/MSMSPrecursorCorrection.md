

mzML files converted from Thermo Orbitrap raw files have problematic MSMS precursor information.
In some programs (such as TOPPView or XCMS) this is incorrectly used and thus false-positive
metabolites with MSMS spectra could occur. In the worst case, this could lead to incorrect
biological interpretation results. 

An example is shown in incorrectMSMSPrecursorInformation.png. This illustration is from a sample
obtained with targeted MSMS and 2 precursors 449.10666 and 447.09351. It can clearly be seen 
that the MSMS information in 449 suddenly at around 820 seconds no longer has any signal, but 
suddenly some in the area of 447. However, these additional MSMS spectra are not of 447.09351, 
but rather of 449.1066 and incorrectly just plotted there. Any tool that would do peak picking
on this dataset and also incorrectly use this wrong precursor MZ would annotate annotate the 
feature 447.11176 with the MSMS spectra of 449.10666. 

Thus, a small python program preprocesses the mzML files and removes these incorrect precursor
mz values. This is done by just deleting the respective tags from the XML file structure. 
After processing the respective sample from above, the MSMS precursor mzs of 449.1066 were 
correctly plotted, which can be seen in correctMSMSPrecursorInformation.png

Please exercise caution using this tool and ideally compare the results to the incorrect ones. 

