#!/bin/bash
# Create exaggerated motion vector visualization with artistic coloring
# Preserves original dimensions and uses high contrast
ffmpeg -flags2 +export_mvs -i "bee4.mp4" -vf "
    codecview=mv=pf+bf+bb,
    
    split=3[base][bloom][trail];
    
    [base]eq=contrast=2.5:saturation=2:brightness=0.1,
                hue=h=t*5[base];
    
    [bloom]eq=contrast=3:brightness=0.2:saturation=2.5,
                 dilation,dilation,dilation,
                 gblur=sigma=2.5,
                 hue=h=t*-3[bloom];
    
    [trail]eq=contrast=2:brightness=-0.1,
                 tblend=all_mode=average:all_opacity=0.5,
                 tmix=frames=5:weights='0.5 0.4 0.3 0.2 0.1',
                 hue=h=t*10+180[trail];
    
    [base][bloom]blend=all_mode=screen:all_opacity=0.7[combined];
    [combined][trail]blend=all_mode=screen:all_opacity=0.5,
    
    eq=contrast=2.5:saturation=1.5:gamma=1.2
" -c:v libx264 -preset medium -crf 18 beedffee4.mp4