<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" version="3.16.13-Hannover" minScale="1e+08" maxScale="1000" hasScaleBasedVisibilityFlag="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal enabled="0" fetchMode="0" mode="0">
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
      <resampling enabled="false" zoomedOutResamplingMethod="nearestNeighbour" zoomedInResamplingMethod="nearestNeighbour" maxOversampling="2"/>
    </provider>
    <rasterrenderer band="1" opacity="0.6" classificationMax="500" alphaBand="-1" nodataColor="" classificationMin="0" type="singlebandpseudocolor">
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
        <colorrampshader maximumValue="500" classificationMode="1" clip="0" colorRampType="DISCRETE" minimumValue="0" labelPrecision="0">
          <colorramp name="[source]" type="gradient">
            <prop v="255,255,204,255" k="color1"/>
            <prop v="0,104,55,255" k="color2"/>
            <prop v="0" k="discrete"/>
            <prop v="gradient" k="rampType"/>
            <prop v="0.25;194,230,153,255:0.5;120,198,121,255:0.75;49,163,84,255" k="stops"/>
          </colorramp>
          <item value="0" color="#808080" label="0" alpha="255"/>
          <item value="4.9" color="#ff0000" label="1,0 - 4,9" alpha="255"/>
          <item value="5.9" color="#ff8000" label="5,0 - 5,9" alpha="255"/>
          <item value="6.9" color="#f8da02" label="6,0 - 6,9" alpha="255"/>
          <item value="7.9" color="#ffff00" label="7,0 - 7,9" alpha="255"/>
          <item value="8.9" color="#00c000" label="8,0 - 8,9" alpha="255"/>
          <item value="9.9" color="#008000" label="9,0 - 9,9" alpha="255"/>
          <item value="11.9" color="#00ffff" label="10,0 - 11,9" alpha="255"/>
          <item value="13.9" color="#00c0c0" label="12,0 - 13,9" alpha="255"/>
          <item value="16.9" color="#0000ff" label="14,0 - 16,9" alpha="255"/>
          <item value="19.9" color="#000080" label="17,0 - 19,9" alpha="255"/>
          <item value="23.9" color="#c000c0" label="20 - 23,9" alpha="255"/>
          <item value="500" color="#800080" label="> 24" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast gamma="1" contrast="0" brightness="0"/>
    <huesaturation grayscaleMode="0" colorizeOn="0" colorizeRed="255" colorizeGreen="128" saturation="0" colorizeStrength="100" colorizeBlue="128"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
