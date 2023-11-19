<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" version="3.22.12-Białowieża" minScale="1e+08" styleCategories="AllStyleCategories" maxScale="-4.65661e-10">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
    <Private>0</Private>
  </flags>
  <temporal fetchMode="0" enabled="1" mode="0">
    <fixedRange>
      <start>2022-12-10T18:56:00Z</start>
      <end>2022-12-10T19:00:00Z</end>
    </fixedRange>
  </temporal>
  <customproperties>
    <Option type="Map">
      <Option value="false" name="WMSBackgroundLayer" type="QString"/>
      <Option value="false" name="WMSPublishDataSourceUrl" type="QString"/>
      <Option value="0" name="embeddedWidgets/count" type="QString"/>
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
      <resampling zoomedOutResamplingMethod="nearestNeighbour" zoomedInResamplingMethod="nearestNeighbour" maxOversampling="2" enabled="false"/>
    </provider>
    <rasterrenderer alphaBand="-1" nodataColor="" type="paletted" band="1" opacity="0.6">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <colorPalette>
        <paletteEntry value="0" color="#f0f0f0" label="Radarbereich" alpha="128"/>
        <paletteEntry value="1" color="#d3d3d3" label="kein Niederschlag" alpha="255"/>
        <paletteEntry value="2" color="#787878" label="nicht klassifizierbar" alpha="255"/>
        <paletteEntry value="3" color="#87cfeb" label="Sprühregen" alpha="255"/>
        <paletteEntry value="4" color="#000099" label="Regen" alpha="255"/>
        <paletteEntry value="5" color="#009900" label="Schneeregen" alpha="255"/>
        <paletteEntry value="6" color="#ffff00" label="Schnee" alpha="255"/>
        <paletteEntry value="7" color="#ff9900" label="Graupel" alpha="255"/>
        <paletteEntry value="8" color="#ff0000" label="Hagel" alpha="255"/>
      </colorPalette>
      <colorramp name="[source]" type="randomcolors">
        <Option/>
      </colorramp>
    </rasterrenderer>
    <brightnesscontrast gamma="1" brightness="0" contrast="0"/>
    <huesaturation grayscaleMode="0" colorizeOn="0" colorizeGreen="128" colorizeBlue="128" saturation="0" colorizeRed="255" colorizeStrength="100" invertColors="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
