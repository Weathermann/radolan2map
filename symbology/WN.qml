<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" version="3.22.12-Białowieża" styleCategories="AllStyleCategories" maxScale="0" minScale="1e+08">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal enabled="1" fetchMode="0" mode="0">
    <fixedRange>
      <start>2022-12-24T21:56:00Z</start>
      <end>2022-12-24T22:00:00Z</end>
    </fixedRange>
  </temporal>
  <customproperties>
    <Option type="Map">
      <Option value="false" name="WMSBackgroundLayer" type="bool"/>
      <Option value="false" name="WMSPublishDataSourceUrl" type="bool"/>
      <Option value="0" name="embeddedWidgets/count" type="int"/>
      <Option value="Value" name="identify/format" type="QString"/>
    </Option>
  </customproperties>
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option value="" name="name" type="QString"/>
      <Option name="properties"/>
      <Option value="collection" name="type" type="QString"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling zoomedOutResamplingMethod="nearestNeighbour" enabled="false" maxOversampling="2" zoomedInResamplingMethod="nearestNeighbour"/>
    </provider>
    <rasterrenderer band="1" opacity="0.6" alphaBand="-1" classificationMin="0" type="singlebandpseudocolor" nodataColor="" classificationMax="85">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader colorRampType="DISCRETE" clip="0" labelPrecision="1" classificationMode="1" minimumValue="0" maximumValue="85">
          <colorramp name="[source]" type="gradient">
            <Option type="Map">
              <Option value="230,230,230,128" name="color1" type="QString"/>
              <Option value="255,51,255,255" name="color2" type="QString"/>
              <Option value="0" name="discrete" type="QString"/>
              <Option value="gradient" name="rampType" type="QString"/>
              <Option value="0.0647059;153,255,255,255:0.117647;51,255,255,255:0.170588;0,202,202,255:0.223529;0,153,52,255:0.276471;77,191,26,255:0.329412;153,204,0,255:0.382353;204,230,0,255:0.435294;255,255,0,255:0.488235;255,196,0,255:0.541176;255,137,0,255:0.594118;255,0,0,255:0.647059;180,0,0,255:0.705882;72,72,255,255:0.764706;0,0,202,255:0.882353;153,0,153,255" name="stops" type="QString"/>
            </Option>
            <prop k="color1" v="230,230,230,128"/>
            <prop k="color2" v="255,51,255,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.0647059;153,255,255,255:0.117647;51,255,255,255:0.170588;0,202,202,255:0.223529;0,153,52,255:0.276471;77,191,26,255:0.329412;153,204,0,255:0.382353;204,230,0,255:0.435294;255,255,0,255:0.488235;255,196,0,255:0.541176;255,137,0,255:0.594118;255,0,0,255:0.647059;180,0,0,255:0.705882;72,72,255,255:0.764706;0,0,202,255:0.882353;153,0,153,255"/>
          </colorramp>
          <item color="#e6e6e6" value="-32.5" label="Radarbereich (no echo)" alpha="128"/>
          <item color="#99ffff" value="5.5" label="bis - 5,4 dBZ" alpha="255"/>
          <item color="#33ffff" value="10" label="5,5 - 10,0 dBZ" alpha="255"/>
          <item color="#00caca" value="14.5" label="10,0 - 14,5 dBZ" alpha="255"/>
          <item color="#009934" value="19" label="14,5 - 19,0 dBZ" alpha="255"/>
          <item color="#4dbf1a" value="23.5" label="19,0 - 23,5 dBZ" alpha="255"/>
          <item color="#99cc00" value="28" label="23,5 - 28,0 dBZ" alpha="255"/>
          <item color="#cce600" value="32.5" label="28,0 - 32,5 dBZ" alpha="255"/>
          <item color="#ffff00" value="37" label="32,5 - 37,0 dBZ" alpha="255"/>
          <item color="#ffc400" value="41.5" label="37,0 - 41,5 dBZ" alpha="255"/>
          <item color="#ff8900" value="46" label="41,5 - 46,0 dBZ" alpha="255"/>
          <item color="#ff0000" value="50.5" label="46,0 - 50,5 dBZ" alpha="255"/>
          <item color="#b40000" value="55" label="50,5 - 55,0 dBZ" alpha="255"/>
          <item color="#4848ff" value="60" label="55,0 - 60,0 dBZ" alpha="255"/>
          <item color="#0000ca" value="65" label="60,0 - 65,0 dBZ" alpha="255"/>
          <item color="#990099" value="75" label="65,0 - 75,0 dBZ" alpha="255"/>
          <item color="#ff33ff" value="85" label="75,0 - 85,0 dBZ" alpha="255"/>
          <rampLegendSettings useContinuousLegend="1" prefix="" suffix="" orientation="2" maximumLabel="" direction="0" minimumLabel="">
            <numericFormat id="basic">
              <Option type="Map">
                <Option value="" name="decimal_separator" type="QChar"/>
                <Option value="6" name="decimals" type="int"/>
                <Option value="0" name="rounding_type" type="int"/>
                <Option value="false" name="show_plus" type="bool"/>
                <Option value="true" name="show_thousand_separator" type="bool"/>
                <Option value="false" name="show_trailing_zeros" type="bool"/>
                <Option value="" name="thousand_separator" type="QChar"/>
              </Option>
            </numericFormat>
          </rampLegendSettings>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast contrast="0" gamma="1" brightness="0"/>
    <huesaturation invertColors="0" colorizeGreen="128" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeOn="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
