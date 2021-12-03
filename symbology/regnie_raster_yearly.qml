<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" maxScale="1000" hasScaleBasedVisibilityFlag="0" minScale="1e+08" version="3.16.13-Hannover">
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
    <rasterrenderer classificationMax="10000" classificationMin="0" band="1" nodataColor="" alphaBand="-1" type="singlebandpseudocolor" opacity="0.6">
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
        <colorrampshader clip="0" classificationMode="1" minimumValue="0" colorRampType="DISCRETE" maximumValue="10000" labelPrecision="0">
          <colorramp name="[source]" type="gradient">
            <prop k="color1" v="255,255,204,255"/>
            <prop k="color2" v="0,104,55,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.25;194,230,153,255:0.5;120,198,121,255:0.75;49,163,84,255"/>
          </colorramp>
          <item alpha="255" label="0" value="0" color="#808080"/>
          <item alpha="255" label="1 - 499" value="499" color="#ff0000"/>
          <item alpha="255" label="500 - 599" value="599" color="#ff8000"/>
          <item alpha="255" label="600 - 699" value="699" color="#f8da02"/>
          <item alpha="255" label="700 - 799" value="799" color="#ffff00"/>
          <item alpha="255" label="800 - 899" value="899" color="#00c000"/>
          <item alpha="255" label="900 - 999" value="999" color="#008000"/>
          <item alpha="255" label="1000 - 1199" value="1199" color="#00ffff"/>
          <item alpha="255" label="1200 - 1399" value="1399" color="#00c0c0"/>
          <item alpha="255" label="1400 - 1699" value="1699" color="#0000ff"/>
          <item alpha="255" label="1700 - 1999" value="1999" color="#000080"/>
          <item alpha="255" label="2000 - 2399" value="2399" color="#c000c0"/>
          <item alpha="255" label="> 2400" value="10000" color="#800080"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast contrast="0" gamma="1" brightness="0"/>
    <huesaturation grayscaleMode="0" saturation="0" colorizeGreen="128" colorizeRed="255" colorizeBlue="128" colorizeOn="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
