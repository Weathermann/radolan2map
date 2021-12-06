<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis maxScale="1000" version="3.16.13-Hannover" hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal enabled="0" mode="0" fetchMode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property value="false" key="WMSBackgroundLayer"/>
    <property value="false" key="WMSPublishDataSourceUrl"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property value="Value" key="identify/format"/>
  </customproperties>
  <pipe>
    <provider>
      <resampling zoomedInResamplingMethod="nearestNeighbour" enabled="false" zoomedOutResamplingMethod="nearestNeighbour" maxOversampling="2"/>
    </provider>
    <rasterrenderer alphaBand="-1" nodataColor="" type="singlebandpseudocolor" opacity="0.6" classificationMin="0" band="1" classificationMax="1000">
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
        <colorrampshader maximumValue="1000" labelPrecision="0" classificationMode="1" minimumValue="0" clip="0" colorRampType="DISCRETE">
          <colorramp type="gradient" name="[source]">
            <prop v="255,255,204,255" k="color1"/>
            <prop v="0,104,55,255" k="color2"/>
            <prop v="0" k="discrete"/>
            <prop v="gradient" k="rampType"/>
            <prop v="0.25;194,230,153,255:0.5;120,198,121,255:0.75;49,163,84,255" k="stops"/>
          </colorramp>
          <item value="0" label="0" alpha="255" color="#808080"/>
          <item value="49.9" label="0,1 - 49,9" alpha="255" color="#ff0000"/>
          <item value="59.9" label="50 - 59,9" alpha="255" color="#ff8000"/>
          <item value="69.9" label="60 - 69,9" alpha="255" color="#f8da02"/>
          <item value="79.9" label="70 - 79,9" alpha="255" color="#ffff00"/>
          <item value="89.9" label="80 - 89,9" alpha="255" color="#00c000"/>
          <item value="99.9" label="90 - 99,9" alpha="255" color="#008000"/>
          <item value="119.9" label="100 - 119,9" alpha="255" color="#00ffff"/>
          <item value="139.9" label="120 - 139,9" alpha="255" color="#00c0c0"/>
          <item value="169.9" label="140 - 169,9" alpha="255" color="#0000ff"/>
          <item value="199.9" label="170 - 199,9" alpha="255" color="#000080"/>
          <item value="239.9" label="200 - 239,9" alpha="255" color="#c000c0"/>
          <item value="1000" label="> 240" alpha="255" color="#800080"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast gamma="1" brightness="0" contrast="0"/>
    <huesaturation colorizeOn="0" colorizeBlue="128" colorizeStrength="100" grayscaleMode="0" saturation="0" colorizeGreen="128" colorizeRed="255"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
