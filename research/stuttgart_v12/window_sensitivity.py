#!/usr/bin/env python3
"""V12 source-figure window sensitivity; raw CSV extends beyond visible Fig2b x-axis.
Not a refutation of published fitting; contrasts two predeclared calibration windows.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.optimize import least_squares
root=Path(__file__).resolve().parent
p=root.parent/'stuttgart_v11/calibration_data/Fig2bdata.csv'
assert hashlib.md5(p.read_bytes()).hexdigest()=='b56696a90f7e19eaf74e4efaf77371ce'
data=np.genfromtxt(p,delimiter=',',skip_header=1)
assert len(data)==24 and data[:,0].max()==2910
def fit_rows(rows):
 t=rows[:,0]*.001
 def fit(y):
  z=least_squares(lambda z:z[0]+z[1]*np.exp(-.5*(z[2]*t)**2)-y,[.5,.5,1],
   bounds=([0,0,.0001],[2,2,20]),
   xtol=1e-12,ftol=1e-12,gtol=1e-12).x
  e=float(np.sqrt(np.mean((z[0]+z[1]*np.exp(-.5*(z[2]*t)**2)-y)**2)))
  return z,e
 prior,ep=fit(rows[:,2]);after,ea=fit(rows[:,1])
 return {'records':len(rows),'time_range_ns':[float(min(rows[:,0])),float(max(rows[:,0]))],
  'prior_sigma_rad_per_us':float(prior[2]),'post_sigma_rad_per_us':float(after[2]),
  'ratio_gaussian_exponent_coefficients_pre_over_post':float((prior[2]/after[2])**2),
  'prior_fit_rmse':ep,'post_fit_rmse':ea}
all_data=fit_rows(data)
visible=fit_rows(data[data[:,0]<=2000])
assert visible['records']==16 and abs(all_data['ratio_gaussian_exponent_coefficients_pre_over_post']-3.8153)<.01
assert abs(visible['ratio_gaussian_exponent_coefficients_pre_over_post']-5.4577)<.02
out={'source':'Original DaRUS Fig2b original bytes + published Figure2b x-axis 0..2000ns',
 'all_source_csv_rows':all_data,'within_published_visible_x_axis':visible,
 'plot_window_extra_source_rows':8,
 'interpretation':'Descriptive Gaussian rate ratio is sensitive to chosen fitting window, not an established microscopic parameter; no formal uncertainty from published per-shot events.',
 'holdout':'Fig3b sealed'}
(root/'window_sensitivity_results.json').write_text(json.dumps(out,indent=2)+'\n')
print('WINDOW_SENSITIVITY',json.dumps(out))
