<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" minScale="1e+08" version="3.6.2-Noosa" maxScale="-4.65661e-10" hasScaleBasedVisibilityFlag="0">
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
    <rasterrenderer type="singlebandpseudocolor" classificationMin="-1" alphaBand="-1" opacity="1" classificationMax="200" band="1">
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
        <colorrampshader colorRampType="INTERPOLATED" clip="0" classificationMode="1">
          <colorramp type="gradient" name="[source]">
            <prop v="255,255,204,255" k="color1"/>
            <prop v="0,104,55,255" k="color2"/>
            <prop v="0" k="discrete"/>
            <prop v="gradient" k="rampType"/>
            <prop v="0.25;194,230,153,255:0.5;120,198,121,255:0.75;49,163,84,255" k="stops"/>
          </colorramp>
          <item alpha="0" value="-1" label="mm" color="#ffffff"/>
          <item alpha="179" value="0" label="0" color="#e6e6e6"/>
          <item alpha="204" value="1" label="bis 1" color="#ffff33"/>
          <item alpha="230" value="2" label="bis 2" color="#33ff33"/>
          <item alpha="255" value="5" label="bis 5" color="#009900"/>
          <item alpha="255" value="10" label="bis 10" color="#80b3ff"/>
          <item alpha="255" value="20" label="bis 20" color="#0066ff"/>
          <item alpha="255" value="50" label="bis 50" color="#8000ff"/>
          <item alpha="255" value="80" label="bis 80" color="#ff00bf"/>
          <item alpha="255" value="200" label="> 80" color="#ffbff0"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeRed="255" colorizeBlue="128" colorizeOn="0" colorizeStrength="100" saturation="0" grayscaleMode="0"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
