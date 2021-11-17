<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis minScale="1e+08" hasScaleBasedVisibilityFlag="0" maxScale="-4.65661e-10" version="3.6.2-Noosa" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <customproperties>
    <property key="WMSBackgroundLayer" value="false"/>
    <property key="WMSPublishDataSourceUrl" value="false"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="identify/format" value="Value"/>
  </customproperties>
  <pipe>
    <rasterrenderer alphaBand="-1" classificationMin="-1" type="singlebandpseudocolor" opacity="1" band="1" classificationMax="100">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Exact</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader classificationMode="1" clip="0" colorRampType="INTERPOLATED">
          <colorramp type="gradient" name="[source]">
            <prop k="color1" v="255,255,204,255"/>
            <prop k="color2" v="0,104,55,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.25;194,230,153,255:0.5;120,198,121,255:0.75;49,163,84,255"/>
          </colorramp>
          <item color="#ffffff" label="mm/h" value="-1" alpha="0"/>
          <item color="#e6e6e6" label="0" value="0" alpha="128"/>
          <item color="#ffffa0" label="bis 0,5" value="0.5" alpha="191"/>
          <item color="#ffff00" label="bis 1" value="1" alpha="255"/>
          <item color="#00ff00" label="bis 2" value="2" alpha="255"/>
          <item color="#80b3ff" label="bis 5" value="5" alpha="255"/>
          <item color="#5010ff" label="bis 10" value="10" alpha="255"/>
          <item color="#ff00bf" label="bis 20" value="20" alpha="255"/>
          <item color="#ffbff0" label="bis 50" value="50" alpha="255"/>
          <item color="#ffffff" label="> 50" value="100" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="0"/>
    <huesaturation colorizeRed="255" colorizeBlue="128" colorizeStrength="100" colorizeOn="0" saturation="0" colorizeGreen="128" grayscaleMode="0"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
