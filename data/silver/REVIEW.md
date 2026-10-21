# Silver label spot-check

For each criterion: read the description, open the PDF at the page number shown
(the PDF viewer's page number, not the number printed on the page), decide yourself, then
compare with the draft. Mark **agree** or **disagree**, and if you disagree write what you
would label and which page proves it.

PDFs: `data/pdfs/<case_id>.pdf`

## USGS-SDG-030: A stormwater management model for the West Branch Brandywine Creek, Chester County, Pennsylvania

- Target: West Branch Brandywine rainfall-runoff model (technology)
- Organizer TRL estimate: 5; draft labeller's opinion: 6
- Draft mode: blind

| Criterion | Draft | Pages | Agree? | Your label / page |
|---|---|---|---|---|
| APCTT-C01 | met | 13, 14, 16 |  |  |
| APCTT-C02 | met | 9, 10 |  |  |
| APCTT-C03 | met | 40, 20 |  |  |
| APCTT-C04 | insufficient evidence | - |  |  |
| APCTT-C05 | met | 9, 20, 40 |  |  |
| APCTT-C06 | met | 25, 9, 32 |  |  |
| APCTT-C07 | insufficient evidence | - |  |  |
| APCTT-C08 | insufficient evidence | - |  |  |
| APCTT-C09 | insufficient evidence | - |  |  |
| APCTT-C10 | insufficient evidence | - |  |  |
| APCTT-C11 | met | 19, 18, 20 |  |  |
| APCTT-C12 | met | 9, 39 |  |  |

**APCTT-C01**: Basic principles (TRL 1): the report states the scientific or engineering principles on which the assessed technology is based, citing observations, studies or literature.

- Draft: **met**. Model basis: physical laws, Green and Ampt infiltration (p14), kinematic wave routing (p16), with citations.
- Quote (page 13): "It is a digital model that uses a deterministic mathematical approach based on approximation of physical laws."

**APCTT-C02**: Concept formulated (TRL 2): the report describes a practical application of those principles and how the assessed technology is intended to work in it.

- Draft: **met**. Practical application (county stormwater management) and how the model is used (p10).
- Quote (page 9): "This investigation, done in cooperation with the Chester County Water Resources Authority, has two purposes: (1) to determine the feasibility of rainfall-runoff modeling in the Brandywine Creek basin based on available data; and (2) to provide a calibrated model for stormwater management by Chester County."

**APCTT-C03**: Proof of concept (TRL 3): the report presents analytical or laboratory results that demonstrate the critical function or characteristic of the assessed technology.

- Draft: **met**. Simulation results demonstrate the model's key function (reproducing storm runoff) and its feasibility.
- Quote (page 40): "Rainfall-runoff modeling with available data is feasible if a recording rain gage is located in the basin or subbasin being modeled."

**APCTT-C04**: Laboratory validation (TRL 4): the report states that the assessed component or a low-fidelity breadboard was tested in a laboratory environment and reports the results.

- Draft: **insufficient evidence**. No laboratory or controlled testing.

**APCTT-C05**: Relevant-environment validation (TRL 5): the report states that the assessed component or breadboard was tested in a simulated or relevant environment representative of the intended environment, and reports the results.

- Draft: **met**. Calibration and verification against observed storms in the subbasins themselves; errors reported (38 percent calibration, 24 percent verification for Modena peak discharge). Honeybrook could not be calibrated; Coatesville calibrated but not verified.
- Quote (page 9): "The Modena subbasin was calibrated and verified."

**APCTT-C06**: Prototype in relevant environment (TRL 6): the report states that a representative model or prototype of the assessed system or subsystem was demonstrated in a relevant environment.

- Draft: **met**. The calibrated models were applied in the real basin to evaluate population growth and proposed flood-control structures. Hyphenation in the PDF text reads 'sub-basins'.
- Quote (page 25): "Predictive simulations were made for the Coatesville and Modena sub-basins with selected storms."

**APCTT-C07**: Prototype in operational environment (TRL 7): the report states that a prototype close to the final configuration was demonstrated in the actual operational environment.

- Draft: **insufficient evidence**. Intended for county use, but no operational use is reported.

**APCTT-C08**: System qualified (TRL 8): the report states that the final system was completed and qualified through test and demonstration against its requirements.

- Draft: **insufficient evidence**. No final qualified system.

**APCTT-C09**: Proven in operation (TRL 9): the report states that the final system was used successfully in actual operations or deployment over a stated period.

- Draft: **insufficient evidence**. No operational record.

**APCTT-C10**: Quantified results against requirements: the report compares measured performance with stated requirements or acceptance criteria and says whether they were met.

- Draft: **insufficient evidence**. Borderline: p20 says Coatesville errors 'were not acceptable' and recalibrated, but no acceptance criterion is stated.

**APCTT-C11**: Environment and test article defined: the report describes the test conditions and the configuration or fidelity of the tested article (for example breadboard, prototype, production unit) relative to the intended application.

- Draft: **met**. Model configuration per subbasin and the storm sets (dates, peak ranges) used for calibration and verification.
- Quote (page 19): "The Coatesville subbasin is described by 38 overland flow segments, 18 channel segments, two reservoir segments, and one input-hydrograph point."

**APCTT-C12**: Evidence matches the assessment target: the cited evidence concerns the assessed target itself (component, subsystem, system or technology), not a different element or only the parent project as a whole.

- Draft: **met**. All evidence concerns the West Branch Brandywine rainfall-runoff model.
- Quote (page 9): "The Modena subbasin was calibrated and verified."

---

## USGS-SDG-096: Digital Shoreline Analysis System (DSAS) version 5.1 user guide

- Target: DSAS v5.1 core shoreline-change rate calculations (technology)
- Organizer TRL estimate: 8; draft labeller's opinion: 8
- Draft mode: blind

| Criterion | Draft | Pages | Agree? | Your label / page |
|---|---|---|---|---|
| APCTT-C01 | met | 27, 25, 69 |  |  |
| APCTT-C02 | met | 15 |  |  |
| APCTT-C03 | met | 69, 66, 67 |  |  |
| APCTT-C04 | met | 23, 15 |  |  |
| APCTT-C05 | met | 104, 91, 21 |  |  |
| APCTT-C06 | met | 114, 104, 106 |  |  |
| APCTT-C07 | met | 5, 42 |  |  |
| APCTT-C08 | met | 15, 23 |  |  |
| APCTT-C09 | insufficient evidence | - |  |  |
| APCTT-C10 | insufficient evidence | - |  |  |
| APCTT-C11 | met | 15, 21, 16 |  |  |
| APCTT-C12 | met | 15 |  |  |

**APCTT-C01**: Basic principles (TRL 1): the report states the scientific or engineering principles on which the assessed technology is based, citing observations, studies or literature.

- Draft: **met**. Statistical basis of the rate calculations (baseline method, regression statistics with uncertainty), with citations.
- Quote (page 27): "DSAS uses a measurement baseline method (Leatherman and Clow, 1983) to cal-culate rate-of-change statistics for a time series of shorelines."

**APCTT-C02**: Concept formulated (TRL 2): the report describes a practical application of those principles and how the assessed technology is intended to work in it.

- Draft: **met**. Application and how the tool works (transects, rate calculations, reliability statistics).
- Quote (page 15): "The Digital Shoreline Analysis System version 5 software is an add-in to Esri ArcGIS Desktop version 10.4–10.7 that enables a user to calculate rate-of-change statistics from a time series of vector shoreline positions."

**APCTT-C03**: Proof of concept (TRL 3): the report presents analytical or laboratory results that demonstrate the critical function or characteristic of the assessed technology.

- Draft: **met**. Worked examples show the core rate statistics being computed.
- Quote (page 69): "In the example illustrated in figure 38, the reported LRR is 1.34 m/yr and the 95-percent confidence interval of the slope (LCI95) is 0.50."

**APCTT-C04**: Laboratory validation (TRL 4): the report states that the assessed component or a low-fidelity breadboard was tested in a laboratory environment and reports the results.

- Draft: **met**. Borderline: software tested in a controlled setting (compatibility testing) with the result stated; no other lab-type testing.
- Quote (page 23): "DSAS v5.1 has been tested for compatibility with ArcGIS 10.4, 10.5, 10.6, and 10.7."

**APCTT-C05**: Relevant-environment validation (TRL 5): the report states that the assessed component or breadboard was tested in a simulated or relevant environment representative of the intended environment, and reports the results.

- Draft: **met**. Run on real shoreline datasets (Outer Banks, Cape Cod) in the intended ArcGIS environment, with results reported (summary report p91-95).
- Quote (page 104): "If the user follows this sample workflow, the results (TRANSECT_rates_datestamp and TRANSECT_intersects_dat-estamp) should appear as follows in figure 4.2."

**APCTT-C06**: Prototype in relevant environment (TRL 6): the report states that a representative model or prototype of the assessed system or subsystem was demonstrated in a relevant environment.

- Draft: **met**. The released system demonstrated end to end on real sample data.
- Quote (page 114): "The results returned to the map, if the user follows this sample workflow, should appear as follows in figure 4.4."

**APCTT-C07**: Prototype in operational environment (TRL 7): the report states that a prototype close to the final configuration was demonstrated in the actual operational environment.

- Draft: **met**. In use by a global user community and in USGS national shoreline-change assessments (p42).
- Quote (page 5): "DSAS version 5 is a culmination of many years of collaborative effort to refine the functionality of the software to meet the needs of a global user base."

**APCTT-C08**: System qualified (TRL 8): the report states that the final system was completed and qualified through test and demonstration against its requirements.

- Draft: **met**. Final released version with stated system requirements and compatibility testing.
- Quote (page 15): "DSAS version 5.1 (v5.1) was released in October 2021, has been tested for compatibility with ArcGIS versions 10.4–10.7, and is supported on Windows 7 and Windows 10 operating systems."

**APCTT-C09**: Proven in operation (TRL 9): the report states that the final system was used successfully in actual operations or deployment over a stated period.

- Draft: **insufficient evidence**. Borderline: DSAS has 25 years of history (p5), but successful operation of this release over a stated period is not reported.

**APCTT-C10**: Quantified results against requirements: the report compares measured performance with stated requirements or acceptance criteria and says whether they were met.

- Draft: **insufficient evidence**. No measured performance against stated requirements.

**APCTT-C11**: Environment and test article defined: the report describes the test conditions and the configuration or fidelity of the tested article (for example breadboard, prototype, production unit) relative to the intended application.

- Draft: **met**. Version, system requirements and the sample datasets used are described.
- Quote (page 15): "Before installing the DSAS v5.1 application, ensure that your system meets the following requirements (installation of new applications will require administrative rights)."

**APCTT-C12**: Evidence matches the assessment target: the cited evidence concerns the assessed target itself (component, subsystem, system or technology), not a different element or only the parent project as a whole.

- Draft: **met**. The evidence is about DSAS v5.1 itself.
- Quote (page 15): "DSAS computes rate-of-change statistics for a time series of shoreline vector data."

---

## USGS-SDG-007: Estimation, distribution, and development of a surrogate model for Escherichia coli in the New River, New River Gorge National Park and Preserve, West Virginia, 2021–23

- Target: New River turbidity-based E. coli surrogate model (technology)
- Organizer TRL estimate: 5; draft labeller's opinion: 6
- Draft mode: assisted

| Criterion | Draft | Pages | Agree? | Your label / page |
|---|---|---|---|---|
| APCTT-C01 | met | 38 |  |  |
| APCTT-C02 | met | 12, 11 |  |  |
| APCTT-C03 | met | 31, 11 |  |  |
| APCTT-C04 | insufficient evidence | - |  |  |
| APCTT-C05 | met | 31, 30, 35 |  |  |
| APCTT-C06 | met | 33 |  |  |
| APCTT-C07 | insufficient evidence | - |  |  |
| APCTT-C08 | insufficient evidence | - |  |  |
| APCTT-C09 | insufficient evidence | - |  |  |
| APCTT-C10 | met | 31 |  |  |
| APCTT-C11 | met | 11, 16, 14 |  |  |
| APCTT-C12 | met | 11, 38 |  |  |

**APCTT-C01**: Basic principles (TRL 1): the report states the scientific or engineering principles on which the assessed technology is based, citing observations, studies or literature.

- Draft: **met**. Surrogate relation basis with citations.
- Quote (page 38): "Turbidity and E. coli relations have been used in this way in many other studies, including Lawrence (2012), Brady and others (2009), and Brady and Plona (2012)."

**APCTT-C02**: Concept formulated (TRL 2): the report describes a practical application of those principles and how the assessed technology is intended to work in it.

- Draft: **met**. Intended application for park staff and visitors.
- Quote (page 12): "The purpose of this report is to document the collection and analysis of water-quality parameters and E. coli concentrations in NERI and to develop a near-real-time surrogate model to estimate E. coli concentrations and provide timely information to National Park staff and visitors about the risks associated with using the New River recreationally."

**APCTT-C03**: Proof of concept (TRL 3): the report presents analytical or laboratory results that demonstrate the critical function or characteristic of the assessed technology.

- Draft: **met**. Analytical results of the regression model.
- Quote (page 31): "For the E. coli recreational-contact standard of 320 MPN/100 mL, the antecedent mean 24-hour turbidity at Thurmond would be estimated by the surrogate model at 23.6 FNU, with a 95-percent confidence interval estimate of 19.4–30.7 FNU."

**APCTT-C04**: Laboratory validation (TRL 4): the report states that the assessed component or a low-fidelity breadboard was tested in a laboratory environment and reports the results.

- Draft: **insufficient evidence**. Laboratory analysis of water samples is data collection, not testing of the model.

**APCTT-C05**: Relevant-environment validation (TRL 5): the report states that the assessed component or breadboard was tested in a simulated or relevant environment representative of the intended environment, and reports the results.

- Draft: **met**. Model developed and checked against field samples from the river itself; estimated vs measured concentrations (fig. 13, p35).
- Quote (page 31): "Residuals (fig. 11) had a standard error of 0.469 and were skewed toward lower values but still passed the Shapiro-Wilk’s test for normality with a p-value of 0.0998 (normality p-value greater than 0.05 for this test)."

**APCTT-C06**: Prototype in relevant environment (TRL 6): the report states that a representative model or prototype of the assessed system or subsystem was demonstrated in a relevant environment.

- Draft: **met**. Borderline: the model was run over the 2-year continuous record at Thurmond.
- Quote (page 33): "This time-series plot of the surrogate model also indicates that exceedances of the recreational-contact standard were infrequent, with antecedent mean 24-hour turbidity exceeding the 23.6 FNU threshold about 18 times during this 2-year period."

**APCTT-C07**: Prototype in operational environment (TRL 7): the report states that a prototype close to the final configuration was demonstrated in the actual operational environment.

- Draft: **insufficient evidence**. The model 'could help' staff; no operational use is reported (p33 discusses future near-real-time use).

**APCTT-C08**: System qualified (TRL 8): the report states that the final system was completed and qualified through test and demonstration against its requirements.

- Draft: **insufficient evidence**. No qualification.

**APCTT-C09**: Proven in operation (TRL 9): the report states that the final system was used successfully in actual operations or deployment over a stated period.

- Draft: **insufficient evidence**. No operational record.

**APCTT-C10**: Quantified results against requirements: the report compares measured performance with stated requirements or acceptance criteria and says whether they were met.

- Draft: **met**. A stated acceptance criterion (p > 0.05) and whether it was met. Exceedances of the E. coli standard are water quality, not model performance.
- Quote (page 31): "Residuals (fig. 11) had a standard error of 0.469 and were skewed toward lower values but still passed the Shapiro-Wilk’s test for normality with a p-value of 0.0998 (normality p-value greater than 0.05 for this test)."

**APCTT-C11**: Environment and test article defined: the report describes the test conditions and the configuration or fidelity of the tested article (for example breadboard, prototype, production unit) relative to the intended application.

- Draft: **met**. Sampling period, monitoring locations and protocols.
- Quote (page 11): "Concentrations of Escherichia coli, a species of fecal-coliform bacteria, were monitored in the New River and selected tributaries from October 2021 through September 2023, with emphasis placed on the primary recreational-contact season from May through October."

**APCTT-C12**: Evidence matches the assessment target: the cited evidence concerns the assessed target itself (component, subsystem, system or technology), not a different element or only the parent project as a whole.

- Draft: **met**. Evidence concerns the New River turbidity-based E. coli surrogate model.
- Quote (page 11): "This surrogate model could help New River Gorge National Park and Preserve staff provide near-real-time information about E. coli concentrations and related recreational-contact risks to the public."

---

## USGS-SDG-077: One-meter topobathymetric digital elevation model for Majuro Atoll, Republic of the Marshall Islands, 1944 to 2016

- Target: Majuro integrated 1-meter topobathymetric DEM workflow (technology)
- Organizer TRL estimate: 6; draft labeller's opinion: 6
- Draft mode: assisted

| Criterion | Draft | Pages | Agree? | Your label / page |
|---|---|---|---|---|
| APCTT-C01 | met | 12, 15 |  |  |
| APCTT-C02 | met | 10 |  |  |
| APCTT-C03 | met | 15, 18 |  |  |
| APCTT-C04 | insufficient evidence | - |  |  |
| APCTT-C05 | met | 10, 20, 18 |  |  |
| APCTT-C06 | met | 21, 10 |  |  |
| APCTT-C07 | insufficient evidence | - |  |  |
| APCTT-C08 | met | 20, 22 |  |  |
| APCTT-C09 | insufficient evidence | - |  |  |
| APCTT-C10 | met | 20, 22, 10 |  |  |
| APCTT-C11 | met | 16, 14, 13 |  |  |
| APCTT-C12 | met | 21, 10 |  |  |

**APCTT-C01**: Basic principles (TRL 1): the report states the scientific or engineering principles on which the assessed technology is based, citing observations, studies or literature.

- Draft: **met**. Principles of structure-from-motion photogrammetry and satellite-derived bathymetry (p15).
- Quote (page 12): "The initial 3D position is refined by iteratively minimizing the geometric error, the projection accuracy error (a relative assessment of matched point accuracy compared to the best matched points), and the reprojection error (differences between the modeled camera locations using the 3D point locations and the real camera locations)."

**APCTT-C02**: Concept formulated (TRL 2): the report describes a practical application of those principles and how the assessed technology is intended to work in it.

- Draft: **met**. Application: inundation modelling, coastal management and hazard adaptation.
- Quote (page 10): "The objective of the project is to collect survey-grade elevation data on Majuro Atoll (fig. 1) to create a topographic digital elevation model (DEM) with a 1-meter (m) horizontal resolution and at least 0.30-m vertical root mean square error (RMSE)"

**APCTT-C03**: Proof of concept (TRL 3): the report presents analytical or laboratory results that demonstrate the critical function or characteristic of the assessed technology.

- Draft: **met**. Results of the processing workflow components.
- Quote (page 15): "Of 71,373 GNSS points, 69,648 (97.5 percent) had SfM point-cloud points within 1 m of each GNSS point location."

**APCTT-C04**: Laboratory validation (TRL 4): the report states that the assessed component or a low-fidelity breadboard was tested in a laboratory environment and reports the results.

- Draft: **insufficient evidence**. No laboratory or controlled testing.

**APCTT-C05**: Relevant-environment validation (TRL 5): the report states that the assessed component or breadboard was tested in a simulated or relevant environment representative of the intended environment, and reports the results.

- Draft: **met**. Validated on the atoll against independent field and lidar data.
- Quote (page 10): "The RMSE of the TBDEM over the land area is 0.197 m using over 70,000 Global Navigation Satellite System (GNSS) real-time kinematic (RTK) survey points for validation, and 1.066 m for Landsat 8 and 1.112 m for WorldView-3 derived bathymetry using over 16,000 and 9,000 lidar bathymetry points, respectively."

**APCTT-C06**: Prototype in relevant environment (TRL 6): the report states that a representative model or prototype of the assessed system or subsystem was demonstrated in a relevant environment.

- Draft: **met**. Workflow applied to produce the full atoll model.
- Quote (page 21): "The final topobathymetric digital elevation model (TBDEM) for Majuro Atoll is derived from various data sources, from charts and soundings to UAS and satellite imagery, spanning over 70 years of data collection on different sections of Majuro Atoll, from 1944 to 2016, and covering an area of 599.6 km2 ."

**APCTT-C07**: Prototype in operational environment (TRL 7): the report states that a prototype close to the final configuration was demonstrated in the actual operational environment.

- Draft: **insufficient evidence**. No operational use of the DEM is reported.

**APCTT-C08**: System qualified (TRL 8): the report states that the final system was completed and qualified through test and demonstration against its requirements.

- Draft: **met**. Literal reading: the final product was checked against published standards. Ladder gap: C07 is not shown, so the TRL opinion stays 6.
- Quote (page 20): "The Majuro Atoll TBDEM, (1) has a 1-m resolution, (2) covers a total area of 599.6 km2 , (3) is compliant with the IHO (2008) published standards of vertical accuracy for bathymetry, and (4) satisfies the USGS National Geospatial Program (NGP) lidar base specifications (Heidemann, 2014) for quality level 3 data for topography"

**APCTT-C09**: Proven in operation (TRL 9): the report states that the final system was used successfully in actual operations or deployment over a stated period.

- Draft: **insufficient evidence**. No operational record.

**APCTT-C10**: Quantified results against requirements: the report compares measured performance with stated requirements or acceptance criteria and says whether they were met.

- Draft: **met**. Measured accuracy (0.197 m RMSE) compared with the stated 0.30 m objective and published standards, and met.
- Quote (page 20): "The Majuro Atoll TBDEM, (1) has a 1-m resolution, (2) covers a total area of 599.6 km2 , (3) is compliant with the IHO (2008) published standards of vertical accuracy for bathymetry, and (4) satisfies the USGS National Geospatial Program (NGP) lidar base specifications (Heidemann, 2014) for quality level 3 data for topography"

**APCTT-C11**: Environment and test article defined: the report describes the test conditions and the configuration or fidelity of the tested article (for example breadboard, prototype, production unit) relative to the intended application.

- Draft: **met**. Data sources, processing thresholds (p14) and field survey dates (p13) described.
- Quote (page 16): "To minimize interpolation artifacts, the priority of input topographic SfM and bathymetric SOPAC, SDB, and chart sounding data were determined based on a variety of project data requirements, such as quality, age, accuracy, and coverage."

**APCTT-C12**: Evidence matches the assessment target: the cited evidence concerns the assessed target itself (component, subsystem, system or technology), not a different element or only the parent project as a whole.

- Draft: **met**. Evidence concerns the Majuro TBDEM workflow and product.
- Quote (page 21): "The final topobathymetric digital elevation model (TBDEM) for Majuro Atoll is derived from various data sources, from charts and soundings to UAS and satellite imagery, spanning over 70 years of data collection on different sections of Majuro Atoll, from 1944 to 2016, and covering an area of 599.6 km2 ."

---

## USGS-SDG-089: Monitoring storm tide and flooding from Hurricane Sandy along the Atlantic coast of the United States, October 2012

- Target: Sandy storm-tide field monitoring and data-delivery system (system)
- Organizer TRL estimate: 9; draft labeller's opinion: 9
- Draft mode: assisted

| Criterion | Draft | Pages | Agree? | Your label / page |
|---|---|---|---|---|
| APCTT-C01 | met | 7 |  |  |
| APCTT-C02 | met | 9, 5 |  |  |
| APCTT-C03 | insufficient evidence | - |  |  |
| APCTT-C04 | insufficient evidence | - |  |  |
| APCTT-C05 | met | 7 |  |  |
| APCTT-C06 | met | 5, 7 |  |  |
| APCTT-C07 | met | 5, 9 |  |  |
| APCTT-C08 | insufficient evidence | - |  |  |
| APCTT-C09 | met | 5, 9 |  |  |
| APCTT-C10 | insufficient evidence | - |  |  |
| APCTT-C11 | met | 7, 9 |  |  |
| APCTT-C12 | met | 5, 9 |  |  |

**APCTT-C01**: Basic principles (TRL 1): the report states the scientific or engineering principles on which the assessed technology is based, citing observations, studies or literature.

- Draft: **met**. Borderline: the measurement basis (pressure-derived water level corrected for barometric pressure and salinity) with cited protocols.
- Quote (page 7): "Data were collected and processed following protocols established by McGee and others (2006) and expanded upon by McCallum and others (2012), which included correcting water pressure for changes in barometric pressure and salinity."

**APCTT-C02**: Concept formulated (TRL 2): the report describes a practical application of those principles and how the assessed technology is intended to work in it.

- Draft: **met**. Application of the monitoring and data-delivery system (FEMA mission, recovery and rebuilding, p5).
- Quote (page 9): "The data can be used to evaluate the performance of storm-tide models for maximum and incremental water level and flood extent, and for site-specific effects of storm tide on natural and anthropo-genic features of the environment."

**APCTT-C03**: Proof of concept (TRL 3): the report presents analytical or laboratory results that demonstrate the critical function or characteristic of the assessed technology.

- Draft: **insufficient evidence**. No separate analytical or laboratory demonstration; for a deployed system experts may still judge lower levels met (open question Q1).

**APCTT-C04**: Laboratory validation (TRL 4): the report states that the assessed component or a low-fidelity breadboard was tested in a laboratory environment and reports the results.

- Draft: **insufficient evidence**. No laboratory testing reported.

**APCTT-C05**: Relevant-environment validation (TRL 5): the report states that the assessed component or breadboard was tested in a simulated or relevant environment representative of the intended environment, and reports the results.

- Draft: **met**. Borderline: checks against independent gages and high-water marks in the field; detailed results are not reported.
- Quote (page 7): "Quality-control checks were made by (1) deploying redundant sensors at a subset of sites, (2) comparing water levels computed from temporary sensors to water levels recorded at nearby USGS streamgaging and NOAA and USGS tidal stations, and (3) comparing elevations to independent high-water marks where possible."

**APCTT-C06**: Prototype in relevant environment (TRL 6): the report states that a representative model or prototype of the assessed system or subsystem was demonstrated in a relevant environment.

- Draft: **met**. System deployed along the coast.
- Quote (page 5): "In response, a total of 162 water-level and wave-height sensors were deployed at 147 locations during October 26–29 prior to landfall."

**APCTT-C07**: Prototype in operational environment (TRL 7): the report states that a prototype close to the final configuration was demonstrated in the actual operational environment.

- Draft: **met**. Used in the actual operational environment (a landfalling hurricane) under a FEMA mission; data delivered through the storm-tide mapper (p9).
- Quote (page 5): "The U.S. Geological Survey (USGS) deployed a temporary monitoring network of water-level and barometric pressure sensors at 224 locations along the Atlantic coast from Virginia to Maine to continuously record the timing, areal extent, and magnitude of hurricane storm tide and coastal flooding generated by Hurricane Sandy (fig. 1)."

**APCTT-C08**: System qualified (TRL 8): the report states that the final system was completed and qualified through test and demonstration against its requirements.

- Draft: **insufficient evidence**. Survey accuracy is reported, but no qualification of the system against requirements.

**APCTT-C09**: Proven in operation (TRL 9): the report states that the final system was used successfully in actual operations or deployment over a stated period.

- Draft: **met**. Repeated successful operational deployments (Irene 2011, Sandy 2012) following established protocols; Irene sites reused (p9).
- Quote (page 5): "This represented the second largest deployment of storm-tide sensors, behind only Hurricane Irene which made landfall in the same vicinity in August 2011."

**APCTT-C10**: Quantified results against requirements: the report compares measured performance with stated requirements or acceptance criteria and says whether they were met.

- Draft: **insufficient evidence**. Vertical accuracy (0.26 ft at 95 percent) is computed by a national standard method, but no required accuracy is stated.

**APCTT-C11**: Environment and test article defined: the report describes the test conditions and the configuration or fidelity of the tested article (for example breadboard, prototype, production unit) relative to the intended application.

- Draft: **met**. Sensor configuration, sampling intervals and datum surveys.
- Quote (page 7): "Of the 162 water-level sensors, 145 sensors were programmed to record water pressure at 30-second intervals, and 9 sensors recorded wave-height measured every 2 seconds, both expressed as water level in feet above the North American Vertical Datum of 1988 (NAVD 88) following surveys completed during sensor recovery."

**APCTT-C12**: Evidence matches the assessment target: the cited evidence concerns the assessed target itself (component, subsystem, system or technology), not a different element or only the parent project as a whole.

- Draft: **met**. Evidence concerns the Sandy storm-tide monitoring and data-delivery system.
- Quote (page 5): "In response, a total of 162 water-level and wave-height sensors were deployed at 147 locations during October 26–29 prior to landfall."

---

