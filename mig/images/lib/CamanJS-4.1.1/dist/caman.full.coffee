# Look what you make me do Javascript
slice = Array::slice

# DOM simplifier (no jQuery dependency)
# NodeJS compatible
$ = (sel, root = document) ->
  return sel if typeof sel is "object" or exports?
  root.querySelector sel

class Util
  # Unique value utility
  @uniqid = do ->
    id = 0
    get: -> id++

  # Helper function that extends one object with all the properies of other objects
  @extend = (obj) ->
    dest = obj
    src = slice.call arguments, 1

    for copy in src
      for own prop of copy
        dest[prop] = copy[prop]

    return dest

  # In order to stay true to the latest spec, RGB values must be clamped between
  # 0 and 255. If we don't do this, weird things happen.
  @clampRGB = (val) ->
    return 0 if val < 0
    return 255 if val > 255
    val

  @copyAttributes: (from, to, opts={}) ->
    for attr in from.attributes
      continue if opts.except? and attr.nodeName in opts.except
      to.setAttribute(attr.nodeName, attr.nodeValue)

  # Support for browsers that don't know Uint8Array (such as IE9)
  @dataArray: (length = 0) ->
    return new Uint8Array(length) if Caman.NodeJS or window.Uint8Array?
    return new Array(length)

# NodeJS compatibility
if exports?
  Root = exports
  Canvas = require 'canvas'
  Image = Canvas.Image

  Fiber = require 'fibers'

  fs = require 'fs'
else
  Root = window

# Here it begins. Caman is defined.
# There are many different initialization for Caman, which are described on the 
# [Basic Usage](http://camanjs.com/docs) page.
#
# Initialization is tricky because we need to make sure everything we need is actually fully 
# loaded in the DOM before proceeding. When initialized on an image, we need to make sure that the 
# image is done loading before converting it to a canvas element and writing the pixel data. If we 
# do this prematurely, the browser will throw a DOM Error, and chaos will ensue. In the event that 
# we initialize Caman on a canvas element while specifying an image URL, we need to create a new 
# image element, load the image, then continue with initialization.
#
# The main goal for Caman was simplicity, so all of this is handled transparently to the end-user. 
Root.Caman = class Caman
  @version:
    release: "4.1.1"
    date: "4/8/2013"

  # Debug mode enables console logging
  @DEBUG: false

  # Are we in a NodeJS environment?
  @NodeJS: exports?

  # Should we check the DOM for images with Caman instructions?
  @autoload: not Caman.NodeJS

  # Allow reverting the canvas?
  # If your JS process is running out of memory, disabling
  # this could help drastically.
  @allowRevert: true

  # Default cross-origin policy
  @crossOrigin: "anonymous"

  @toString: ->
    "Version " + Caman.version.release + ", Released " + Caman.version.date;

  # Set the URL of the image proxy script
  @remoteProxy: ""

  # Change the GET param used with the proxy script if needed
  @proxyParam: "camanProxyUrl"

  @getAttrId: (canvas) ->
    return true if Caman.NodeJS

    if typeof canvas is "string"
      canvas = $(canvas)

    return null unless canvas? and canvas.getAttribute?
    canvas.getAttribute 'data-caman-id'

  constructor: ->
    throw "Invalid arguments" if arguments.length is 0

    if @ instanceof Caman
      # We have to do this to avoid polluting the global scope
      # because of how Coffeescript binds functions specified 
      # with => and the fact that Caman can be invoked as both
      # a function and as a 'new' object.
      @finishInit = @finishInit.bind(@)
      @imageLoaded = @imageLoaded.bind(@)

      args = arguments[0]

      unless Caman.NodeJS
        id = parseInt Caman.getAttrId(args[0]), 10
        callback = if typeof args[1] is "function"
          args[1]
        else if typeof args[2] is "function"
          args[2]
        else
          ->

        if !isNaN(id) and Store.has(id)
          return Store.execute(id, callback)

      # Every instance gets a unique ID. Makes it much simpler to check if two variables are the 
      # same instance.
      @id = Util.uniqid.get()
      
      @initializedPixelData = @originalPixelData = null
      @cropCoordinates = x: 0, y: 0
      @cropped = false
      @resized = false

      @pixelStack = []  # Stores the pixel layers
      @layerStack = []  # Stores all of the layers waiting to be rendered
      @canvasQueue = [] # Stores all of the canvases to be processed
      @currentLayer = null
      @scaled = false

      @analyze = new Analyze @
      @renderer = new Renderer @

      @domIsLoaded =>  
        @parseArguments(args)
        @setup()

      return @
    else
      return new Caman(arguments)

  domIsLoaded: (cb) ->
    if Caman.NodeJS
      setTimeout =>
        cb.call(@)
      , 0
    else
      if document.readyState is "complete"
        Log.debug "DOM initialized"
        setTimeout =>
          cb.call(@)
        , 0
      else
        listener = =>
          if document.readyState is "complete"
            Log.debug "DOM initialized"
            cb.call(@)

        document.addEventListener "readystatechange", listener, false

  # All possible combinations:
  #
  # **1 argument**
  #   - Image selector
  #   - Image object
  #   - Canvas selector
  #   - Canvas object
  #
  # **2 arguments**
  #   - Image selector + callback
  #   - Image object + callback
  #   - Canvas selector + URL
  #   - Canvas object + URL
  #
  # **3 arguments**
  #   - Canvas selector + URL + callback
  #   - Canvas object + URL + callback
  #
  # **NodeJS**
  #   - file path
  #   - file object
  #   - file path + callback
  #   - file object + callback
  parseArguments: (args) ->
    throw "Invalid arguments given" if args.length is 0

    # Defaults
    @initObj = null
    @initType = null
    @imageUrl = null
    @callback = ->

    # First argument is always our canvas/image
    @setInitObject args[0]
    return if args.length is 1
    
    switch typeof args[1]
      when "string" then @imageUrl = args[1]
      when "function" then @callback = args[1]
      
    return if args.length is 2

    @callback = args[2]

    if args.length is 4
      @options[key] = val for own key, val of args[4]

  setInitObject: (obj) ->
    if Caman.NodeJS
      @initObj = obj
      @initType = 'node'
      return

    if typeof obj is "object"
      @initObj = obj
    else
      @initObj = $(obj)

    throw "Could not find image or canvas for initialization." unless @initObj?

    @initType = @initObj.nodeName.toLowerCase()

  setup: ->
    switch @initType
      when "node" then @initNode()
      when "img" then @initImage()
      when "canvas" then @initCanvas()

  initNode: ->
    Log.debug "Initializing for NodeJS"

    @image = new Image()
    @image.onload = =>
      Log.debug "Image loaded. Width = #{@imageWidth()}, Height = #{@imageHeight()}"
      @canvas = new Canvas @imageWidth(), @imageHeight()
      @finishInit()

    @image.onerror = (err) -> throw err
    @image.src = @initObj

  initImage: ->
    @image = @initObj
    @canvas = document.createElement 'canvas'
    @context = @canvas.getContext '2d'
    Util.copyAttributes @image, @canvas, except: ['src']

    @image.parentNode.replaceChild @canvas, @image

    @imageAdjustments()
    @waitForImageLoaded()

  initCanvas: ->
    @canvas = @initObj
    @context = @canvas.getContext '2d'

    if @imageUrl?
      @image = document.createElement 'img'
      @image.src = @imageUrl

      @imageAdjustments()
      @waitForImageLoaded()
    else
      @finishInit()

  imageAdjustments: ->
    if @needsHiDPISwap()
      Log.debug @image.src, "->", @hiDPIReplacement()

      @swapped = true
      @image.src = @hiDPIReplacement()

    if IO.isRemote(@image)
      @image.src = IO.proxyUrl(@image.src)
      Log.debug "Remote image detected, using URL = #{@image.src}"

  waitForImageLoaded: ->
    if @isImageLoaded()
      @imageLoaded()
    else
      @image.onload = @imageLoaded

  isImageLoaded: ->
    return false unless @image.complete
    return false if @image.naturalWidth? and @image.naturalWidth is 0
    return true

  # Internet Explorer has issues figuring out image dimensions when they aren't
  # explicitly defined apparently. We check the normal width/height properties first,
  # but fall back to natural sizes if they are 0.
  imageWidth: -> @image.width or @image.naturalWidth
  imageHeight: -> @image.height or @image.naturalHeight

  imageLoaded: ->
    Log.debug "Image loaded. Width = #{@imageWidth()}, Height = #{@imageHeight()}"

    if @swapped
      @canvas.width = @imageWidth() / @hiDPIRatio()
      @canvas.height = @imageHeight() / @hiDPIRatio()
    else
      @canvas.width = @imageWidth()
      @canvas.height = @imageHeight()

    @finishInit()

  finishInit: ->
    @context = @canvas.getContext '2d' unless @context?

    @originalWidth = @preScaledWidth = @width = @canvas.width
    @originalHeight = @preScaledHeight = @height = @canvas.height

    @hiDPIAdjustments()
    @assignId() unless @hasId()

    if @image?
      @context.drawImage @image, 
        0, 0, 
        @imageWidth(), @imageHeight(), 
        0, 0, 
        @preScaledWidth, @preScaledHeight
    
    @reloadCanvasData()
    
    if Caman.allowRevert
      @initializedPixelData = Util.dataArray(@pixelData.length)
      @originalPixelData = Util.dataArray(@pixelData.length)

      for pixel, i in @pixelData
        @initializedPixelData[i] = pixel
        @originalPixelData[i] = pixel

    @dimensions =
      width: @canvas.width
      height: @canvas.height

    Store.put @id, @

    @callback.call @,@

    # Reset the callback so re-initialization doesn't
    # trigger it again.
    @callback = ->

  # If you have a separate context reference to this canvas outside of CamanJS
  # and you make a change to the canvas outside of CamanJS, you will have to call
  # this function to update our context reference to include those changes.
  reloadCanvasData: ->
    @imageData = @context.getImageData 0, 0, @canvas.width, @canvas.height
    @pixelData = @imageData.data

  resetOriginalPixelData: ->
    throw "Revert disabled" unless Caman.allowRevert

    @originalPixelData = Util.dataArray(@pixelData.length)
    @originalPixelData.push pixel for pixel in @pixelData

  hasId: -> Caman.getAttrId(@canvas)?

  assignId: ->
    return if Caman.NodeJS or @canvas.getAttribute 'data-caman-id'
    @canvas.setAttribute 'data-caman-id', @id

  hiDPIDisabled: ->
    @canvas.getAttribute('data-caman-hidpi-disabled') isnt null

  hiDPIAdjustments: ->
    return if Caman.NodeJS or @hiDPIDisabled()

    ratio = @hiDPIRatio()

    if ratio isnt 1
      Log.debug "HiDPI ratio = #{ratio}"
      @scaled = true

      @preScaledWidth = @canvas.width
      @preScaledHeight = @canvas.height

      @canvas.width = @preScaledWidth * ratio
      @canvas.height = @preScaledHeight * ratio
      @canvas.style.width = "#{@preScaledWidth}px"
      @canvas.style.height = "#{@preScaledHeight}px"

      @context.scale ratio, ratio

      @width = @originalWidth = @canvas.width
      @height = @originalHeight = @canvas.height

  hiDPIRatio: ->
    devicePixelRatio = window.devicePixelRatio or 1
    backingStoreRatio = @context.webkitBackingStorePixelRatio or
                        @context.mozBackingStorePixelRatio or
                        @context.msBackingStorePixelRatio or
                        @context.oBackingStorePixelRatio or
                        @context.backingStorePixelRatio or 1

    devicePixelRatio / backingStoreRatio

  hiDPICapable: -> window.devicePixelRatio? and window.devicePixelRatio isnt 1

  needsHiDPISwap: ->
    return false if @hiDPIDisabled() or !@hiDPICapable()
    @hiDPIReplacement() isnt null

  hiDPIReplacement: ->
    return null unless @image?
    @image.getAttribute 'data-caman-hidpi'

  replaceCanvas: (newCanvas) ->
    oldCanvas = @canvas
    @canvas = newCanvas
    @context = @canvas.getContext '2d'

    oldCanvas.parentNode.replaceChild @canvas, oldCanvas

    @width  = @canvas.width
    @height = @canvas.height

    @reloadCanvasData()

    @dimensions =
      width: @canvas.width
      height: @canvas.height

  # Begins the rendering process
  render: (callback = ->) ->
    Event.trigger @, "renderStart"
    
    @renderer.execute =>
      @context.putImageData @imageData, 0, 0
      callback.call @

  # Reverts the canvas back to it's original state while
  # maintaining any cropped or resized dimensions.
  revert: ->
    throw "Revert disabled" unless Caman.allowRevert

    @pixelData[i] = pixel for pixel, i in @originalVisiblePixels()
    @context.putImageData @imageData, 0, 0

  # Completely resets the canvas back to it's original state.
  # Any size adjustments will also be reset.
  reset: ->
    canvas = document.createElement('canvas')
    Util.copyAttributes(@canvas, canvas)

    canvas.width = @originalWidth
    canvas.height = @originalHeight

    ctx = canvas.getContext('2d')
    imageData = ctx.getImageData 0, 0, canvas.width, canvas.height
    pixelData = imageData.data

    pixelData[i] = pixel for pixel, i in @initializedPixelData

    ctx.putImageData imageData, 0, 0

    @cropCoordinates = x: 0, y: 0
    @resized = false

    @replaceCanvas(canvas)

  # Returns the original pixel data while maintaining any
  # cropping or resizing that may have occured.
  originalVisiblePixels: ->
    throw "Revert disabled" unless Caman.allowRevert

    pixels = []

    startX = @cropCoordinates.x
    endX = startX + @width
    startY = @cropCoordinates.y
    endY = startY + @height

    if @resized
      canvas = document.createElement('canvas')
      canvas.width = @originalWidth
      canvas.height = @originalHeight

      ctx = canvas.getContext('2d')
      imageData = ctx.getImageData 0, 0, canvas.width, canvas.height
      pixelData = imageData.data

      pixelData[i] = pixel for pixel, i in @originalPixelData

      ctx.putImageData imageData, 0, 0

      scaledCanvas = document.createElement('canvas')
      scaledCanvas.width = @width
      scaledCanvas.height = @height

      ctx = scaledCanvas.getContext('2d')
      ctx.drawImage canvas, 0, 0, @originalWidth, @originalHeight, 0, 0, @width, @height

      pixelData = ctx.getImageData(0, 0, @width, @height).data
      width = @width
    else
      pixelData = @originalPixelData
      width = @originalWidth

    for i in [0...pixelData.length] by 4
      coord = PixelInfo.locationToCoordinates(i, width)
      if (startX <= coord.x < endX) and (startY <= coord.y < endY)
        pixels.push pixelData[i], 
          pixelData[i+1],
          pixelData[i+2], 
          pixelData[i+3]

    pixels

  # Pushes the filter callback that modifies the RGBA object into the
  # render queue
  process: (name, processFn) ->
    @renderer.add
      type: Filter.Type.Single
      name: name
      processFn: processFn

    return @

  # Pushes the kernel into the render queue
  processKernel: (name, adjust, divisor, bias) ->
    if not divisor
      divisor = 0
      divisor += adjust[i] for i in [0...adjust.length]

    @renderer.add
      type: Filter.Type.Kernel
      name: name
      adjust: adjust
      divisor: divisor
      bias: bias or 0

    return @

  # Adds a standalone plugin into the render queue
  processPlugin: (plugin, args) ->
    @renderer.add
      type: Filter.Type.Plugin
      plugin: plugin
      args: args

    return @

  # Pushes a new layer operation into the render queue and calls the layer
  # callback
  newLayer: (callback) ->
    layer = new Layer @
    @canvasQueue.push layer
    @renderer.add type: Filter.Type.LayerDequeue

    callback.call layer

    @renderer.add type: Filter.Type.LayerFinished
    return @

  # Pushes the layer context and moves to the next operation
  executeLayer: (layer) -> @pushContext layer

  # Set all of the relevant data to the new layer
  pushContext: (layer) ->
    @layerStack.push @currentLayer
    @pixelStack.push @pixelData
    @currentLayer = layer
    @pixelData = layer.pixelData

  # Restore the previous layer context
  popContext: ->
    @pixelData = @pixelStack.pop()
    @currentLayer = @layerStack.pop()

  # Applies the current layer to its parent layer
  applyCurrentLayer: -> @currentLayer.applyToParent()


class Analyze
  constructor: (@c) ->

  calculateLevels: ->
    levels =
      r: {}
      g: {}
      b: {}

    # Initialize all values to 0 first so there are no data gaps
    for i in [0..255]
      levels.r[i] = 0
      levels.g[i] = 0
      levels.b[i] = 0

    # Iterate through each pixel block and increment the level counters
    for i in [0...@c.pixelData.length] by 4
      levels.r[@c.pixelData[i]]++
      levels.g[@c.pixelData[i+1]]++
      levels.b[@c.pixelData[i+2]]++

    # Normalize all of the numbers by converting them to percentages between
    # 0 and 1.0
    numPixels = @c.pixelData.length / 4

    for i in [0..255]
      levels.r[i] /= numPixels
      levels.g[i] /= numPixels
      levels.b[i] /= numPixels

    levels

Caman.DOMUpdated = ->
  imgs = document.querySelectorAll("img[data-caman]")
  return unless imgs.length > 0

  for img in imgs
    parser = new CamanParser img, ->
      @parse()
      @execute()

# If enabled, we check the page to see if there are any
# images with Caman instructions provided using HTML5
# data attributes.
if Caman.autoload then do ->
  if document.readyState is "complete"
    Caman.DOMUpdated()
  else
    document.addEventListener "DOMContentLoaded", Caman.DOMUpdated, false

# Parses Caman instructions embedded in the HTML data-caman attribute
class CamanParser
  INST_REGEX = "(\\w+)\\((.*?)\\)"

  constructor: (ele, ready) ->
    @dataStr = ele.getAttribute('data-caman')
    @caman = Caman ele, ready.bind(@)

  parse: ->
    @ele = @caman.canvas

    # First we find each instruction as a whole using a global
    # regex search.
    r = new RegExp(INST_REGEX, 'g')
    unparsedInstructions = @dataStr.match r
    return unless unparsedInstructions.length > 0

    # Once we gather all the instructions, we go through each one
    # and parse out the filter name + it's parameters.
    r = new RegExp(INST_REGEX)
    for inst in unparsedInstructions
      [m, filter, args] = inst.match(r)

      # Create a factory function so we can catch any errors that
      # are produced when running the filters. This also makes it very
      # simple to support multiple/complex filter arguments.
      instFunc = new Function("return function() {
        this.#{filter}(#{args});
      };")

      try
        func = instFunc()
        func.call @caman
      catch e
        Log.debug e

  execute: ->
    ele = @ele
    @caman.render ->
      ele.parentNode.replaceChild @toImage(), ele

# Built-in layer blenders. Many of these mimic Photoshop blend modes.
Caman.Blender = class Blender
  @blenders = {}

  # Registers a blender. Can be used to add your own blenders outside of
  # the core library, if needed.
  @register: (name, func) -> @blenders[name] = func

  # Executes a blender to combine a layer with its parent.
  @execute: (name, rgbaLayer, rgbaParent) ->
    @blenders[name](rgbaLayer, rgbaParent)

# Various math-heavy helpers
Caman.Calculate = class Calculate
  # Calculates the distance between two points
  @distance: (x1, y1, x2, y2) ->
    Math.sqrt Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2)

  # Generates a pseudorandom number that lies within the max - mix range. The number can be either 
  # an integer or a float depending on what the user specifies.
  @randomRange: (min, max, getFloat = false) ->
    rand = min + (Math.random() * (max - min))
    return if getFloat then rand.toFixed(getFloat) else Math.round(rand)

  # Calculates the luminance of a single pixel using a special weighted sum
  @luminance: (rgba) -> (0.299 * rgba.r) + (0.587 * rgba.g) + (0.114 * rgba.b)

  # Generates a bezier curve given a start and end point, with two control points in between.
  # Can also optionally bound the y values between a low and high bound.
  #
  # This is different than most bezier curve functions because it attempts to construct it in such 
  # a way that we can use it more like a simple input -> output system, or a one-to-one function. 
  # In other words we can provide an input color value, and immediately receive an output modified 
  # color value.
  #
  # Note that, by design, this does not force X values to be in the range [0..255]. This is to
  # generalize the function a bit more. If you give it a starting X value that isn't 0, and/or a
  # ending X value that isn't 255, you may run into problems with your filter!
  @bezier: (start, ctrl1, ctrl2, end, lowBound, highBound) ->
    x0 = start[0]
    y0 = start[1]
    x1 = ctrl1[0]
    y1 = ctrl1[1]
    x2 = ctrl2[0]
    y2 = ctrl2[1]
    x3 = end[0]
    y3 = end[1]
    bezier = {}

    # Calculate our X/Y coefficients
    Cx = parseInt(3 * (x1 - x0), 10)
    Bx = 3 * (x2 - x1) - Cx
    Ax = x3 - x0 - Cx - Bx

    Cy = 3 * (y1 - y0)
    By = 3 * (y2 - y1) - Cy
    Ay = y3 - y0 - Cy - By

    # 1000 is actually arbitrary. We need to make sure we do enough
    # calculations between 0 and 255 that, in even the more extreme
    # circumstances, we calculate as many values as possible. In the event
    # that an X value is skipped, it will be found later on using linear
    # interpolation.
    for i in [0...1000]
      t = i / 1000

      curveX = Math.round (Ax * Math.pow(t, 3)) + (Bx * Math.pow(t, 2)) + (Cx * t) + x0
      curveY = Math.round (Ay * Math.pow(t, 3)) + (By * Math.pow(t, 2)) + (Cy * t) + y0

      if lowBound and curveY < lowBound
        curveY = lowBound
      else if highBound and curveY > highBound
        curveY = highBound

      bezier[curveX] = curveY

    # Do a search for missing values in the bezier array and use linear
    # interpolation to approximate their values
    if bezier.length < end[0] + 1
      for i in [0..end[0]]
        if not bezier[i]?
          leftCoord = [i-1, bezier[i-1]]

          # Find the first value to the right. Ideally this loop will break
          # very quickly.
          for j in [i..end[0]]
            if bezier[j]?
              rightCoord = [j, bezier[j]]
              break

          bezier[i] = leftCoord[1] + 
            ((rightCoord[1] - leftCoord[1]) / (rightCoord[0] - leftCoord[0])) * 
            (i - leftCoord[0])

    # Edge case
    bezier[end[0]] = bezier[end[0] - 1] if not bezier[end[0]]?
    
    return bezier
      

# Tons of color conversion functions
class Convert
  # Converts the hex representation of a color to RGB values.
  # Hex value can optionally start with the hash (#).
  #
  # <pre>
  # @param   String  hex   The colors hex value
  # @return  Array         The RGB representation
  # </pre>
  @hexToRGB: (hex) ->
    hex = hex.substr(1) if hex.charAt(0) is "#"
    r = parseInt hex.substr(0, 2), 16
    g = parseInt hex.substr(2, 2), 16
    b = parseInt hex.substr(4, 2), 16

    r: r, g: g, b: b

  # Converts an RGB color to HSL.
  # Assumes r, g, and b are in the set [0, 255] and
  # returns h, s, and l in the set [0, 1].
  #
  # <pre>
  # @param   Number  r   Red channel
  # @param   Number  g   Green channel
  # @param   Number  b   Blue channel
  # @return              The HSL representation
  # </pre>
  @rgbToHSL: (r, g, b) ->
    if typeof r is "object"
      g = r.g
      b = r.b
      r = r.r

    r /= 255
    g /= 255
    b /= 255

    max = Math.max r, g, b
    min = Math.min r, g, b
    l = (max + min) / 2

    if max is min
      h = s = 0
    else
      d = max - min
      s = if l > 0.5 then d / (2 - max - min) else d / (max + min)
      h = switch max
        when r then (g - b) / d + (if g < b then 6 else 0)
        when g then (b - r) / d + 2
        when b then (r - g) / d + 4
      
      h /= 6

    h: h, s: s, l: l

  # Converts an HSL color value to RGB. Conversion formula
  # adapted from http://en.wikipedia.org/wiki/HSL_color_space.
  # Assumes h, s, and l are contained in the set [0, 1] and
  # returns r, g, and b in the set [0, 255].
  #
  # <pre>
  # @param   Number  h       The hue
  # @param   Number  s       The saturation
  # @param   Number  l       The lightness
  # @return  Array           The RGB representation
  # </pre>
  @hslToRGB: (h, s, l) ->
    if typeof h is "object"
      s = h.s
      l = h.l
      h = h.h

    if s is 0
      r = g = b = l
    else
      q = if l < 0.5 then l * (1 + s) else l + s - l * s
      p = 2 * l - q
      
      r = @hueToRGB p, q, h + 1/3
      g = @hueToRGB p, q, h
      b = @hueToRGB p, q, h - 1/3

    r: r * 255, g: g * 255, b: b * 255

  # Converts from the hue color space back to RGB
  @hueToRGB: (p, q, t) ->
    if t < 0 then t += 1
    if t > 1 then t -= 1
    if t < 1/6 then return p + (q - p) * 6 * t
    if t < 1/2 then return q
    if t < 2/3 then return p + (q - p) * (2/3 - t) * 6
    return p

  # Converts an RGB color value to HSV. Conversion formula
  # adapted from http://en.wikipedia.org/wiki/HSV_color_space.
  # Assumes r, g, and b are contained in the set [0, 255] and
  # returns h, s, and v in the set [0, 1].
  #
  # <pre>
  # @param   Number  r       The red color value
  # @param   Number  g       The green color value
  # @param   Number  b       The blue color value
  # @return  Array           The HSV representation
  # </pre>
  @rgbToHSV: (r, g, b) ->
    r /= 255
    g /= 255
    b /= 255

    max = Math.max r, g, b
    min = Math.min r, g, b
    v = max
    d = max - min

    s = if max is 0 then 0 else d / max

    if max is min
      h = 0
    else
      h = switch max
        when r then (g - b) / d + (if g < b then 6 else 0)
        when g then (b - r) / d + 2
        when b then (r - g) / d + 4

      h /= 6

    h: h, s: s, v: v

  # Converts an HSV color value to RGB. Conversion formula
  # adapted from http://en.wikipedia.org/wiki/HSV_color_space.
  # Assumes h, s, and v are contained in the set [0, 1] and
  # returns r, g, and b in the set [0, 255].
  #
  # <pre>
  # @param   Number  h       The hue
  # @param   Number  s       The saturation
  # @param   Number  v       The value
  # @return  Array           The RGB representation
  # </pre>
  @hsvToRGB: (h, s, v) ->
    i = Math.floor h * 6
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    switch i % 6
      when 0
        r = v
        g = t
        b = p
      when 1
        r = q
        g = v
        b = p
      when 2
        r = p
        g = v
        b = t
      when 3
        r = p
        g = q
        b = v
      when 4
        r = t
        g = p
        b = v
      when 5
        r = v
        g = p
        b = q

    r: r * 255, g: g * 255, b: b * 255

  # Converts a RGB color value to the XYZ color space. Formulas
  # are based on http://en.wikipedia.org/wiki/SRGB assuming that
  # RGB values are sRGB.
  #
  # Assumes r, g, and b are contained in the set [0, 255] and
  # returns x, y, and z.
  #
  # <pre>
  # @param   Number  r       The red color value
  # @param   Number  g       The green color value
  # @param   Number  b       The blue color value
  # @return  Array           The XYZ representation
  # </pre>
  @rgbToXYZ: (r, g, b) ->
    r /= 255
    g /= 255
    b /= 255

    if r > 0.04045
      r = Math.pow((r + 0.055) / 1.055, 2.4)
    else
      r /= 12.92

    if g > 0.04045
      g = Math.pow((g + 0.055) / 1.055, 2.4)
    else
      g /= 12.92

    if b > 0.04045
      b = Math.pow((b + 0.055) / 1.055, 2.4)
    else
      b /= 12.92

    x = r * 0.4124 + g * 0.3576 + b * 0.1805;
    y = r * 0.2126 + g * 0.7152 + b * 0.0722;
    z = r * 0.0193 + g * 0.1192 + b * 0.9505;
  
    x: x * 100, y: y * 100, z: z * 100

  # Converts a XYZ color value to the sRGB color space. Formulas
  # are based on http://en.wikipedia.org/wiki/SRGB and the resulting
  # RGB value will be in the sRGB color space.
  # Assumes x, y and z values are whatever they are and returns
  # r, g and b in the set [0, 255].
  #
  # <pre>
  # @param   Number  x       The X value
  # @param   Number  y       The Y value
  # @param   Number  z       The Z value
  # @return  Array           The RGB representation
  # </pre>
  @xyzToRGB: (x, y, z) ->
    x /= 100
    y /= 100
    z /= 100

    r = (3.2406  * x) + (-1.5372 * y) + (-0.4986 * z)
    g = (-0.9689 * x) + (1.8758  * y) + (0.0415  * z)
    b = (0.0557  * x) + (-0.2040 * y) + (1.0570  * z)

    if r > 0.0031308
      r = (1.055 * Math.pow(r, 0.4166666667)) - 0.055
    else
      r *= 12.92

    if g > 0.0031308
      g = (1.055 * Math.pow(g, 0.4166666667)) - 0.055
    else
      g *= 12.92

    if b > 0.0031308
      b = (1.055 * Math.pow(b, 0.4166666667)) - 0.055
    else
      b *= 12.92

    r: r * 255, g: g * 255, b: b * 255

  # Converts a XYZ color value to the CIELAB color space. Formulas
  # are based on http://en.wikipedia.org/wiki/Lab_color_space
  # The reference white point used in the conversion is D65.
  # Assumes x, y and z values are whatever they are and returns
  # L*, a* and b* values
  #
  # <pre>
  # @param   Number  x       The X value
  # @param   Number  y       The Y value
  # @param   Number  z       The Z value
  # @return  Array           The Lab representation
  # </pre>
  @xyzToLab: (x, y, z) ->
    if typeof x is "object"
      y = x.y
      z = x.z
      x = x.x

    whiteX = 95.047
    whiteY = 100.0
    whiteZ = 108.883

    x /= whiteX
    y /= whiteY
    z /= whiteZ

    if x > 0.008856451679
      x = Math.pow(x, 0.3333333333)
    else
      x = (7.787037037 * x) + 0.1379310345
  
    if y > 0.008856451679
      y = Math.pow(y, 0.3333333333)
    else
      y = (7.787037037 * y) + 0.1379310345
  
    if z > 0.008856451679
      z = Math.pow(z, 0.3333333333)
    else
      z = (7.787037037 * z) + 0.1379310345

    l = 116 * y - 16
    a = 500 * (x - y)
    b = 200 * (y - z)

    l: l, a: a, b: b

  # Converts a L*, a*, b* color values from the CIELAB color space
  # to the XYZ color space. Formulas are based on
  # http://en.wikipedia.org/wiki/Lab_color_space
  #
  # The reference white point used in the conversion is D65.
  # Assumes L*, a* and b* values are whatever they are and returns
  # x, y and z values.
  #
  # <pre>
  # @param   Number  l       The L* value
  # @param   Number  a       The a* value
  # @param   Number  b       The b* value
  # @return  Array           The XYZ representation
  # </pre>
  @labToXYZ: (l, a, b) ->
    if typeof l is "object"
      a = l.a
      b = l.b
      l = l.l

    y = (l + 16) / 116
    x = y + (a / 500)
    z = y - (b / 200)

    if x > 0.2068965517
      x = x * x * x
    else
      x = 0.1284185493 * (x - 0.1379310345)
  
    if y > 0.2068965517
      y = y * y * y
    else
      y = 0.1284185493 * (y - 0.1379310345)
  
    if z > 0.2068965517
      z = z * z * z
    else
      z = 0.1284185493 * (z - 0.1379310345)

    # D65 reference white point
    x: x * 95.047, y: y * 100.0, z: z * 108.883

  @rgbToLab: (r, g, b) ->
    if typeof r is "object"
      g = r.g
      b = r.b
      r = r.r
    
    xyz = @rgbToXYZ(r, g, b)
    @xyzToLab xyz

  @labToRGB: (l, a, b) ->
    

# Event system that can be used to register callbacks that get fired
# during certain times in the render process.
class Event
  @events = {}

  # All of the supported event types
  @types = [
    "processStart"
    "processComplete"
    "renderStart"
    "renderFinished"
    "blockStarted"
    "blockFinished"
  ]

  # Trigger an event
  @trigger: (target, type, data) ->
    if @events[type] and @events[type].length
      for event in @events[type]
        if event.target is null or target.id is event.target.id
          event.fn.call target, data 
  
  # Listen for an event. Optionally bind the listen to a single CamanInstance
  # or all CamanInstances.
  @listen: (target, type, fn) ->
    # Adjust arguments if target is omitted
    if typeof target is "string"
      _type = target
      _fn = type

      target = null
      type = _type
      fn = _fn

    # Validation
    return false if type not in @types

    @events[type] = [] if not @events[type]
    @events[type].push target: target, fn: fn

    return true

Caman.Event = Event

# Responsible for storing all of the filters
Caman.Filter = class Filter
  # All of the different render operatives
  @Type =
    Single: 1
    Kernel: 2
    LayerDequeue: 3
    LayerFinished: 4
    LoadOverlay: 5
    Plugin: 6

  # Registers a filter function
  @register: (name, filterFunc) -> Caman::[name] = filterFunc

# Various I/O based operations
Caman.IO = class IO
  @domainRegex = /(?:(?:http|https):\/\/)((?:\w+)\.(?:(?:\w|\.)+))/

  # Is the given URL remote?
  # If a cross-origin setting is set, we assume you have CORS
  # properly configured.
  @isRemote: (img) ->
    return false unless img?
    return false if @corsEnabled(img)
    return @isURLRemote img.src

  @corsEnabled: (img) ->
    img.crossOrigin? and img.crossOrigin.toLowerCase() in ['anonymous', 'use-credentials']

  @isURLRemote: (url) ->
    matches = url.match @domainRegex
    return if matches then matches[1] isnt document.domain else false

  @remoteCheck: (src) ->
    if @isURLRemote src
      if not Caman.remoteProxy.length
        Log.info "Attempting to load a remote image without a configured proxy. URL: #{src}"
        return
      else
        if Caman.isURLRemote Caman.remoteProxy
          Log.info "Cannot use a remote proxy for loading images."
          return
          
        "#{Caman.remoteProxy}?camanProxyUrl=#{encodeURIComponent(src)}"


  @proxyUrl: (src) ->
    "#{Caman.remoteProxy}?#{Caman.proxyParam}=#{encodeURIComponent(src)}"

  # Shortcut for using one of the bundled proxies.
  @useProxy: (lang) ->
    langToExt =
      ruby: 'rb'
      python: 'py'
      perl: 'pl'
      javascript: 'js'

    lang = lang.toLowerCase()
    lang = langToExt[lang] if langToExt[lang]?
    "proxies/caman_proxy.#{lang}"
  
# Grabs the canvas data, encodes it to Base64, then sets the browser location to 
# the encoded data so that the user will be prompted to download it.
Caman::save = ->
  if exports?
    @nodeSave.apply @, arguments
  else
    @browserSave.apply @, arguments

Caman::browserSave = (type = "png") ->
  type = type.toLowerCase()

  # Force download (its a bit hackish)
  image = @toBase64(type).replace "image/#{type}", "image/octet-stream"
  document.location.href = image

Caman::nodeSave = (file, overwrite = true) ->
  try
    stats = fs.statSync file
    return false if stats.isFile() and not overwrite
  catch e
    Log.debug "Creating output file #{file}"

  fs.writeFile file, @canvas.toBuffer(), ->
    Log.debug "Finished writing to #{file}"

# Takes the current canvas data, converts it to Base64, then sets it as the source 
# of a new Image object and returns it.
Caman::toImage = (type) ->
  img = document.createElement 'img'
  img.src = @toBase64 type
  img.width = @dimensions.width
  img.height = @dimensions.height

  if window.devicePixelRatio
    img.width /= window.devicePixelRatio
    img.height /= window.devicePixelRatio

  return img

# Base64 encodes the current canvas
Caman::toBase64 = (type = "png") ->
  type = type.toLowerCase()
  return @canvas.toDataURL "image/#{type}"


# The entire layering system for Caman resides in this file. Layers get their own canvasLayer 
# objectwhich is created when newLayer() is called. For extensive information regarding the 
# specifics of howthe layering system works, there is an in-depth blog post on this very topic. 
# Instead of copying the entirety of that post, I'll simply point you towards the 
# [blog link](http://blog.meltingice.net/programming/implementing-layers-camanjs).
#
# However, the gist of the layering system is that, for each layer, it creates a new canvas 
# element and then either copies the parent layer's data or applies a solid color to the new 
# layer. After some (optional) effects are applied, the layer is blended back into the parent 
# canvas layer using one of many different blending algorithms.
#
# You can also load an image (local or remote, with a proxy) into a canvas layer, which is useful 
# if you want to add textures to an image.
class Layer
  constructor: (@c) ->
    # Compatibility
    @filter = @c
    
    @options =
      blendingMode: 'normal'
      opacity: 1.0

    # Each layer gets its own unique ID
    @layerID = Util.uniqid.get()

    # Create the canvas for this layer
    @canvas = if exports? then new Canvas() else document.createElement('canvas')
    
    @canvas.width = @c.dimensions.width
    @canvas.height = @c.dimensions.height

    @context = @canvas.getContext('2d')
    @context.createImageData @canvas.width, @canvas.height
    @imageData = @context.getImageData 0, 0, @canvas.width, @canvas.height
    @pixelData = @imageData.data

  # If you want to create nested layers
  newLayer: (cb) -> @c.newLayer.call @c, cb

  # Sets the blending mode of this layer. The mode is the name of a blender function.
  setBlendingMode: (mode) ->
    @options.blendingMode = mode
    return @

  # Sets the opacity of this layer. This affects how much of this layer is applied to the parent
  # layer at render time.
  opacity: (opacity) ->
    @options.opacity = opacity / 100
    return @

  # Copies the contents of the parent layer to this layer
  copyParent: ->
    parentData = @c.pixelData

    for i in [0...@c.pixelData.length] by 4
      @pixelData[i]   = parentData[i]
      @pixelData[i+1] = parentData[i+1]
      @pixelData[i+2] = parentData[i+2]
      @pixelData[i+3] = parentData[i+3]

    return @

  # Fills this layer with a single color
  fillColor: -> @c.fillColor.apply @c, arguments

  # Loads and overlays an image onto this layer
  overlayImage: (image) ->
    if typeof image is "object"
      image = image.src
    else if typeof image is "string" and image[0] is "#"
      image = $(image).src

    return @ if not image

    @c.renderer.renderQueue.push
      type: Filter.Type.LoadOverlay
      src: image
      layer: @

    return @
  
  # Takes the contents of this layer and applies them to the parent layer at render time. This
  # should never be called explicitly by the user.
  applyToParent: ->
    parentData = @c.pixelStack[@c.pixelStack.length - 1]
    layerData = @c.pixelData
    
    for i in [0...layerData.length] by 4
      rgbaParent =
        r: parentData[i]
        g: parentData[i+1]
        b: parentData[i+2]
        a: parentData[i+3]

      rgbaLayer =
        r: layerData[i]
        g: layerData[i+1]
        b: layerData[i+2]
        a: layerData[i+3]

      result = Blender.execute @options.blendingMode, rgbaLayer, rgbaParent

      result.r = Util.clampRGB result.r
      result.g = Util.clampRGB result.g
      result.b = Util.clampRGB result.b
      result.a = rgbaLayer.a if not result.a?

      parentData[i]   = rgbaParent.r - (
        (rgbaParent.r - result.r) * (@options.opacity * (result.a / 255))
      )
      parentData[i+1] = rgbaParent.g - (
        (rgbaParent.g - result.g) * (@options.opacity * (result.a / 255))
      )
      parentData[i+2] = rgbaParent.b - (
        (rgbaParent.b - result.b) * (@options.opacity * (result.a / 255))
      )


# Simple console logger class that can be toggled on and off based on Caman.DEBUG
class Logger
  constructor: ->
    for name in ['log', 'info', 'warn', 'error']
      @[name] = do (name) ->
        (args...) ->
          return if not Caman.DEBUG
          try
            console[name].apply console, args
          catch e
            # We're probably using IE9 or earlier
            console[name] args

    @debug = @log

Log = new Logger()

# This object is available inside of the process() loop, and it lets filter developers have simple 
# access to any arbitrary pixel in the image, as well as information about the current pixel in 
# the loop.
class PixelInfo
  @coordinatesToLocation: (x, y, width) ->
    (y * width + x) * 4

  @locationToCoordinates: (loc, width) ->
    y = Math.floor(loc / (width * 4))
    x = (loc % (width * 4)) / 4

    return x: x, y: y

  constructor: (@c) -> @loc = 0

  # Retrieves the X, Y location of the current pixel. The origin is at the bottom left corner of 
  # the image, like a normal coordinate system.
  locationXY: ->
    y = @c.dimensions.height - Math.floor(@loc / (@c.dimensions.width * 4))
    x = (@loc % (@c.dimensions.width * 4)) / 4

    return x: x, y: y

  # Returns an RGBA object for a pixel whose location is specified in relation to the current 
  # pixel.
  getPixelRelative: (horiz, vert) ->
    # We invert the vert_offset in order to make the coordinate system non-inverted. In laymans
    # terms: -1 means down and +1 means up.
    newLoc = @loc + (@c.dimensions.width * 4 * (vert * -1)) + (4 * horiz)

    if newLoc > @c.pixelData.length or newLoc < 0
      return r: 0, g: 0, b: 0, a: 0

    return {
      r: @c.pixelData[newLoc]
      g: @c.pixelData[newLoc + 1]
      b: @c.pixelData[newLoc + 2]
      a: @c.pixelData[newLoc + 3]
    }

  # The counterpart to getPixelRelative, this updates the value of a pixel whose location is 
  # specified in relation to the current pixel.
  putPixelRelative: (horiz, vert, rgba) ->
    nowLoc = @loc + (@c.dimensions.width * 4 * (vert * -1)) + (4 * horiz)

    return if newLoc > @c.pixelData.length or newLoc < 0

    @c.pixelData[newLoc] = rgba.r
    @c.pixelData[newLoc + 1] = rgba.g
    @c.pixelData[newLoc + 2] = rgba.b
    @c.pixelData[newLoc + 3] = rgba.a

    return true

  # Gets an RGBA object for an arbitrary pixel in the canvas specified by absolute X, Y coordinates
  getPixel: (x, y) ->
    loc = @coordinatesToLocation(x, y, @width)

    return {
      r: @c.pixelData[loc]
      g: @c.pixelData[loc + 1]
      b: @c.pixelData[loc + 2]
      a: @c.pixelData[loc + 3]
    }

  # Updates the pixel at the given X, Y coordinate
  putPixel: (x, y, rgba) ->
    loc = @coordinatesToLocation(x, y, @width)

    @c.pixelData[loc] = rgba.r
    @c.pixelData[loc + 1] = rgba.g
    @c.pixelData[loc + 2] = rgba.b
    @c.pixelData[loc + 3] = rgba.a


# Stores and registers standalone plugins
class Plugin
  @plugins = {}

  @register: (name, plugin) -> @plugins[name] = plugin
  @execute: (context, name, args) -> @plugins[name].apply context, args

Caman.Plugin = Plugin

# Handles all of the various rendering methods in Caman. Most of the image modification happens 
# here. A new Renderer object is created for every render operation.
Caman.Renderer = class Renderer
  # The number of blocks to split the image into during the render process to simulate 
  # concurrency. This also helps the browser manage the (possibly) long running render jobs.
  @Blocks = if Caman.NodeJS then require('os').cpus().length else 4

  constructor: (@c) ->
    @renderQueue = []
    @modPixelData = null

  add: (job) ->
    return unless job?
    @renderQueue.push job

  # Grabs the next operation from the render queue and passes it to Renderer
  # for execution
  processNext: =>
    # If the queue is empty, fire the finished callback
    if @renderQueue.length is 0
      Event.trigger @, "renderFinished"
      @finishedFn.call(@c) if @finishedFn?

      return @

    @currentJob = @renderQueue.shift()

    switch @currentJob.type
      when Filter.Type.LayerDequeue
        layer = @c.canvasQueue.shift()
        @c.executeLayer layer
        @processNext()
      when Filter.Type.LayerFinished
        @c.applyCurrentLayer()
        @c.popContext()
        @processNext()
      when Filter.Type.LoadOverlay
        @loadOverlay @currentJob.layer, @currentJob.src
      when Filter.Type.Plugin
        @executePlugin()
      else
        @executeFilter()

  execute: (callback) ->
    @finishedFn = callback
    @modPixelData = Util.dataArray(@c.pixelData.length)

    @processNext()

  eachBlock: (fn) ->
    # Prepare all the required render data
    @blocksDone = 0

    n = @c.pixelData.length
    blockPixelLength = Math.floor (n / 4) / Renderer.Blocks
    blockN = blockPixelLength * 4
    lastBlockN = blockN + ((n / 4) % Renderer.Blocks) * 4

    for i in [0...Renderer.Blocks]
      start = i * blockN
      end = start + (if i is Renderer.Blocks - 1 then lastBlockN else blockN)

      if Caman.NodeJS
        f = Fiber => fn.call(@, i, start, end)
        bnum = f.run()
        @blockFinished(bnum)
      else
        setTimeout do (i, start, end) =>
          => fn.call(@, i, start, end)
        , 0

  # The core of the image rendering, this function executes the provided filter.
  #
  # NOTE: this does not write the updated pixel data to the canvas. That happens when all filters 
  # are finished rendering in order to be as fast as possible.
  executeFilter: ->
    Event.trigger @c, "processStart", @currentJob

    if @currentJob.type is Filter.Type.Single
      @eachBlock @renderBlock
    else
      @eachBlock @renderKernel

  # Executes a standalone plugin
  executePlugin: ->
    Log.debug "Executing plugin #{@currentJob.plugin}"
    Plugin.execute @c, @currentJob.plugin, @currentJob.args
    Log.debug "Plugin #{@currentJob.plugin} finished!"

    @processNext()

  # Renders a single block of the canvas with the current filter function
  renderBlock: (bnum, start, end) ->
    Log.debug "Block ##{bnum} - Filter: #{@currentJob.name}, Start: #{start}, End: #{end}"
    Event.trigger @c, "blockStarted",
      blockNum: bnum
      totalBlocks: Renderer.Blocks
      startPixel: start
      endPixel: end

    data = r: 0, g: 0, b: 0, a: 0
    pixelInfo = new PixelInfo @c

    for i in [start...end] by 4
      pixelInfo.loc = i

      data.r = @c.pixelData[i]
      data.g = @c.pixelData[i+1]
      data.b = @c.pixelData[i+2]
      data.a = @c.pixelData[i+3]

      res = @currentJob.processFn.call pixelInfo, data
      res.a = data.a if not res.a?

      @c.pixelData[i]   = Util.clampRGB res.r
      @c.pixelData[i+1] = Util.clampRGB res.g
      @c.pixelData[i+2] = Util.clampRGB res.b
      @c.pixelData[i+3] = Util.clampRGB res.a

    if Caman.NodeJS
      Fiber.yield(bnum)
    else
      @blockFinished bnum

  # Applies an image kernel to the canvas
  renderKernel: (bnum, start, end) ->
    name = @currentJob.name
    bias = @currentJob.bias
    divisor = @currentJob.divisor
    n = @c.pixelData.length

    adjust = @currentJob.adjust
    adjustSize = Math.sqrt adjust.length

    kernel = []

    Log.debug "Rendering kernel - Filter: #{@currentJob.name}"

    start = Math.max start, @c.dimensions.width * 4 * ((adjustSize - 1) / 2)
    end = Math.min end, n - (@c.dimensions.width * 4 * ((adjustSize - 1) / 2))

    builder = (adjustSize - 1) / 2

    pixelInfo = new PixelInfo @c

    for i in [start...end] by 4
      pixelInfo.loc = i
      builderIndex = 0

      for j in [-builder..builder]
        for k in [builder..-builder]
          pixel = pixelInfo.getPixelRelative j, k
          kernel[builderIndex * 3]     = pixel.r
          kernel[builderIndex * 3 + 1] = pixel.g
          kernel[builderIndex * 3 + 2] = pixel.b

          builderIndex++

      res = @processKernel adjust, kernel, divisor, bias

      @modPixelData[i]    = Util.clampRGB(res.r)
      @modPixelData[i+1]  = Util.clampRGB(res.g)
      @modPixelData[i+2]  = Util.clampRGB(res.b)
      @modPixelData[i+3]  = @c.pixelData[i+3]

    if Caman.NodeJS
      Fiber.yield(bnum)
    else
      @blockFinished bnum

  # Called when a single block is finished rendering. Once all blocks are done, we signal that this
  # filter is finished rendering and continue to the next step.
  blockFinished: (bnum) ->
    Log.debug "Block ##{bnum} finished! Filter: #{@currentJob.name}" if bnum >= 0
    @blocksDone++

    Event.trigger @c, "blockFinished",
      blockNum: bnum
      blocksFinished: @blocksDone
      totalBlocks: Renderer.Blocks

    if @blocksDone is Renderer.Blocks
      if @currentJob.type is Filter.Type.Kernel
        for i in [0...@c.pixelData.length]
          @c.pixelData[i] = @modPixelData[i]

      Log.debug "Filter #{@currentJob.name} finished!" if bnum >=0
      Event.trigger @c, "processComplete", @currentJob

      @processNext()

  # The "filter function" for kernel adjustments.
  processKernel: (adjust, kernel, divisor, bias) ->
    val = r: 0, g: 0, b: 0

    for i in [0...adjust.length]
      val.r += adjust[i] * kernel[i * 3]
      val.g += adjust[i] * kernel[i * 3 + 1]
      val.b += adjust[i] * kernel[i * 3 + 2]

    val.r = (val.r / divisor) + bias
    val.g = (val.g / divisor) + bias
    val.b = (val.b / divisor) + bias
    val

  # Loads an image onto the current canvas
  loadOverlay: (layer, src) ->
    img = document.createElement 'img'
    img.onload = =>
      layer.context.drawImage img, 0, 0, @c.dimensions.width, @c.dimensions.height
      layer.imageData = layer.context.getImageData 0, 0, @c.dimensions.width, @c.dimensions.height
      layer.pixelData = layer.imageData.data

      @c.pixelData = layer.pixelData

      @processNext()

    proxyUrl = IO.remoteCheck src
    img.src = if proxyUrl? then proxyUrl else src

# Used for storing instances of CamanInstance objects such that, when Caman() is called on an 
# already initialized element, it returns that object instead of re-initializing.
Caman.Store = class Store
  @items = {}
  
  @has: (search) -> @items[search]?
  @get: (search) -> @items[search]
  @put: (name, obj) -> @items[name] = obj
  @execute: (search, callback) ->
    setTimeout =>
      callback.call @get(search), @get(search)
    , 0

    return @get(search)
    
  @flush: (name = false) ->
    if name then delete @items[name] else @items = {}

# Directly apply the child layer's pixels to the parent layer with no special changes
Blender.register "normal", (rgbaLayer, rgbaParent) ->
  r: rgbaLayer.r
  g: rgbaLayer.g
  b: rgbaLayer.b

# Apply the child to the parent by multiplying the color values. This generally creates contrast.
Blender.register "multiply", (rgbaLayer, rgbaParent) ->
  r: (rgbaLayer.r * rgbaParent.r) / 255
  g: (rgbaLayer.g * rgbaParent.g) / 255
  b: (rgbaLayer.b * rgbaParent.b) / 255

Blender.register "screen", (rgbaLayer, rgbaParent) ->
  r: 255 - (((255 - rgbaLayer.r) * (255 - rgbaParent.r)) / 255)
  g: 255 - (((255 - rgbaLayer.g) * (255 - rgbaParent.g)) / 255)
  b: 255 - (((255 - rgbaLayer.b) * (255 - rgbaParent.b)) / 255)
  

Blender.register "overlay", (rgbaLayer, rgbaParent) ->
  result = {}
  result.r = 
    if rgbaParent.r > 128
      255 - 2 * (255 - rgbaLayer.r) * (255 - rgbaParent.r) / 255
    else (rgbaParent.r * rgbaLayer.r * 2) / 255

  result.g =
    if rgbaParent.g > 128
      255 - 2 * (255 - rgbaLayer.g) * (255 - rgbaParent.g) / 255
    else (rgbaParent.g * rgbaLayer.g * 2) / 255

  result.b =
    if rgbaParent.b > 128
      255 - 2 * (255 - rgbaLayer.b) * (255 - rgbaParent.b) / 255
    else (rgbaParent.b * rgbaLayer.b * 2) / 255

  result

Blender.register "difference", (rgbaLayer, rgbaParent) ->
  r: rgbaLayer.r - rgbaParent.r
  g: rgbaLayer.g - rgbaParent.g
  b: rgbaLayer.b - rgbaParent.b

Blender.register "addition", (rgbaLayer, rgbaParent) ->
  r: rgbaParent.r + rgbaLayer.r
  g: rgbaParent.g + rgbaLayer.g
  b: rgbaParent.b + rgbaLayer.b

Blender.register "exclusion", (rgbaLayer, rgbaParent) ->
  r: 128 - 2 * (rgbaParent.r - 128) * (rgbaLayer.r - 128) / 255
  g: 128 - 2 * (rgbaParent.g - 128) * (rgbaLayer.g - 128) / 255
  b: 128 - 2 * (rgbaParent.b - 128) * (rgbaLayer.b - 128) / 255

Blender.register "softLight", (rgbaLayer, rgbaParent) ->
  result = {}

  result.r =
    if rgbaParent.r > 128
      255 - ((255 - rgbaParent.r) * (255 - (rgbaLayer.r - 128))) / 255
    else (rgbaParent.r * (rgbaLayer.r + 128)) / 255

  result.g =
    if rgbaParent.g > 128
      255 - ((255 - rgbaParent.g) * (255 - (rgbaLayer.g - 128))) / 255
    else (rgbaParent.g * (rgbaLayer.g + 128)) / 255

  result.b =
    if rgbaParent.b > 128
      255 - ((255 - rgbaParent.b) * (255 - (rgbaLayer.b - 128))) / 255
    else (rgbaParent.b * (rgbaLayer.b + 128)) / 255

  result

Blender.register "lighten", (rgbaLayer, rgbaParent) ->
  r: if rgbaParent.r > rgbaLayer.r then rgbaParent.r else rgbaLayer.r
  g: if rgbaParent.g > rgbaLayer.g then rgbaParent.g else rgbaLayer.g
  b: if rgbaParent.b > rgbaLayer.b then rgbaParent.b else rgbaLayer.b

Blender.register "darken", (rgbaLayer, rgbaParent) ->
  r: if rgbaParent.r > rgbaLayer.r then rgbaLayer.r else rgbaParent.r
  g: if rgbaParent.g > rgbaLayer.g then rgbaLayer.g else rgbaParent.g
  b: if rgbaParent.b > rgbaLayer.b then rgbaLayer.b else rgbaParent.b

# The filters define all of the built-in functionality that comes with Caman (as opposed to being 
# provided by a plugin). All of these filters are ratherbasic, but are extremely powerful when
# many are combined. For information on creating plugins, check out the 
# [Plugin Creation](http://camanjs.com/docs/plugin-creation) page, and for information on using 
# the plugins, check out the [Built-In Functionality](http://camanjs.com/docs/built-in) page.

# ## Fill Color
# Fills the canvas with a single solid color.
# 
# ### Arguments
# Can take either separate R, G, and B values as arguments, or a single hex color value.
Filter.register "fillColor", ->
  if arguments.length is 1
    color = Convert.hexToRGB arguments[0]
  else
    color =
      r: arguments[0]
      g: arguments[1]
      b: arguments[2]

  @process "fillColor", (rgba) ->
    rgba.r = color.r
    rgba.g = color.g
    rgba.b = color.b
    rgba.a = 255
    rgba

# ## Brightness
# Simple brightness adjustment
#
# ### Arguments
# Range is -100 to 100. Values < 0 will darken image while values > 0 will brighten.
Filter.register "brightness", (adjust) ->
  adjust = Math.floor 255 * (adjust / 100)

  @process "brightness", (rgba) ->
    rgba.r += adjust
    rgba.g += adjust
    rgba.b += adjust
    rgba

# ## Saturation
# Adjusts the color saturation of the image.
#
# ### Arguments
# Range is -100 to 100. Values < 0 will desaturate the image while values > 0 will saturate it.
# **If you want to completely desaturate the image**, using the greyscale filter is highly 
# recommended because it will yield better results.
Filter.register "saturation", (adjust) ->
  adjust *= -0.01

  @process "saturation", (rgba) ->
    max = Math.max rgba.r, rgba.g, rgba.b

    rgba.r += (max - rgba.r) * adjust if rgba.r isnt max
    rgba.g += (max - rgba.g) * adjust if rgba.g isnt max
    rgba.b += (max - rgba.b) * adjust if rgba.b isnt max
    rgba

# ## Vibrance
# Similar to saturation, but adjusts the saturation levels in a slightly smarter, more subtle way. 
# Vibrance will attempt to boost colors that are less saturated more and boost already saturated
# colors less, while saturation boosts all colors by the same level.
#
# ### Arguments
# Range is -100 to 100. Values < 0 will desaturate the image while values > 0 will saturate it.
# **If you want to completely desaturate the image**, using the greyscale filter is highly 
# recommended because it will yield better results.
Filter.register "vibrance", (adjust) ->
  adjust *= -1

  @process "vibrance", (rgba) ->
    max = Math.max rgba.r, rgba.g, rgba.b
    avg = (rgba.r + rgba.g + rgba.b) / 3
    amt = ((Math.abs(max - avg) * 2 / 255) * adjust) / 100

    rgba.r += (max - rgba.r) * amt if rgba.r isnt max
    rgba.g += (max - rgba.g) * amt if rgba.g isnt max
    rgba.b += (max - rgba.b) * amt if rgba.b isnt max
    rgba
    
# ## Greyscale
# An improved greyscale function that should make prettier results
# than simply using the saturation filter to remove color. It does so by using factors
# that directly relate to how the human eye perceves color and values. There are
# no arguments, it simply makes the image greyscale with no in-between.
#
# Algorithm adopted from http://www.phpied.com/image-fun/
Filter.register "greyscale", (adjust) ->
  @process "greyscale", (rgba) ->
    # Calculate the average value of the 3 color channels 
    # using the special factors
    avg = Calculate.luminance(rgba)

    rgba.r = avg
    rgba.g = avg
    rgba.b = avg
    rgba

# ## Contrast
# Increases or decreases the color contrast of the image.
#
# ### Arguments
# Range is -100 to 100. Values < 0 will decrease contrast while values > 0 will increase contrast.
# The contrast adjustment values are a bit sensitive. While unrestricted, sane adjustment values 
# are usually around 5-10.
Filter.register "contrast", (adjust) ->
  adjust = Math.pow((adjust + 100) / 100, 2)

  @process "contrast", (rgba) ->
    # Red channel
    rgba.r /= 255;
    rgba.r -= 0.5;
    rgba.r *= adjust;
    rgba.r += 0.5;
    rgba.r *= 255;
    
    # Green channel
    rgba.g /= 255;
    rgba.g -= 0.5;
    rgba.g *= adjust;
    rgba.g += 0.5;
    rgba.g *= 255;
    
    # Blue channel
    rgba.b /= 255;
    rgba.b -= 0.5;
    rgba.b *= adjust;
    rgba.b += 0.5;
    rgba.b *= 255;

    rgba

# ## Hue
# Adjusts the hue of the image. It can be used to shift the colors in an image in a uniform 
# fashion. If you are unfamiliar with Hue, I recommend reading this 
# [Wikipedia article](http://en.wikipedia.org/wiki/Hue).
#
# ### Arguments
# Range is 0 to 100
# Sometimes, Hue is expressed in the range of 0 to 360. If that's the terminology you're used to, 
# think of 0 to 100 representing the percentage of Hue shift in the 0 to 360 range.
Filter.register "hue", (adjust) ->
  @process "hue", (rgba) ->
    hsv = Convert.rgbToHSV rgba.r, rgba.g, rgba.b
    
    h = hsv.h * 100
    h += Math.abs adjust
    h = h % 100
    h /= 100
    hsv.h = h

    rgb = Convert.hsvToRGB hsv.h, hsv.s, hsv.v
    rgb.a = rgba.a
    rgb

# ## Colorize
# Uniformly shifts the colors in an image towards the given color. The adjustment range is from 0 
# to 100. The higher the value, the closer the colors in the image shift towards the given 
# adjustment color.
#
# ### Arguments
# This filter is polymorphic and can take two different sets of arguments. Either a hex color 
# string and an adjustment value, or RGB colors and an adjustment value.
Filter.register "colorize", ->
  if arguments.length is 2
    rgb = Convert.hexToRGB(arguments[0])
    level = arguments[1]
  else if arguments.length is 4
    rgb =
      r: arguments[0]
      g: arguments[1]
      b: arguments[2]

    level = arguments[3]

  @process "colorize", (rgba) ->
    rgba.r -= (rgba.r - rgb.r) * (level / 100)
    rgba.g -= (rgba.g - rgb.g) * (level / 100)
    rgba.b -= (rgba.b - rgb.b) * (level / 100)
    rgba

# ## Invert
# Inverts all colors in the image by subtracting each color channel value from 255. No arguments.
Filter.register "invert", ->
  @process "invert", (rgba) ->
    rgba.r = 255 - rgba.r
    rgba.g = 255 - rgba.g
    rgba.b = 255 - rgba.b
    rgba
    
# ## Sepia
# Applies an adjustable sepia filter to the image.
#
# ### Arguments
# Assumes adjustment is between 0 and 100, which represents how much the sepia filter is applied.
Filter.register "sepia", (adjust = 100) ->
  adjust /= 100

  @process "sepia", (rgba) ->
     # All three color channels have special conversion factors that 
     # define what sepia is. Here we adjust each channel individually, 
     # with the twist that you can partially apply the sepia filter.
    rgba.r = Math.min(255, (rgba.r * (1 - (0.607 * adjust))) + (rgba.g * (0.769 * adjust)) + (rgba.b * (0.189 * adjust)));
    rgba.g = Math.min(255, (rgba.r * (0.349 * adjust)) + (rgba.g * (1 - (0.314 * adjust))) + (rgba.b * (0.168 * adjust)));
    rgba.b = Math.min(255, (rgba.r * (0.272 * adjust)) + (rgba.g * (0.534 * adjust)) + (rgba.b * (1- (0.869 * adjust))));

    rgba

# ## Gamma
# Adjusts the gamma of the image.
#
# ### Arguments
# Range is from 0 to infinity, although sane values are from 0 to 4 or 5.
# Values between 0 and 1 will lessen the contrast while values greater than 1 will increase it.
Filter.register "gamma", (adjust) ->
  @process "gamma", (rgba) ->
    rgba.r = Math.pow(rgba.r / 255, adjust) * 255
    rgba.g = Math.pow(rgba.g / 255, adjust) * 255
    rgba.b = Math.pow(rgba.b / 255, adjust) * 255
    rgba

# ## Noise
# Adds noise to the image on a scale from 1 - 100. However, the scale isn't constrained, so you 
# can specify a value > 100 if you want a LOT of noise.
Filter.register "noise", (adjust) ->
  adjust = Math.abs(adjust) * 2.55
  
  @process "noise", (rgba) ->
    rand = Calculate.randomRange adjust * -1, adjust

    rgba.r += rand
    rgba.g += rand
    rgba.b += rand
    rgba

# ## Clip
# Clips a color to max values when it falls outside of the specified range.
#
# ### Arguments
# Supplied value should be between 0 and 100.
Filter.register "clip", (adjust) ->
  adjust = Math.abs(adjust) * 2.55

  @process "clip", (rgba) ->
    if rgba.r > 255 - adjust
      rgba.r = 255
    else if rgba.r < adjust
      rgba.r = 0

    if rgba.g > 255 - adjust
      rgba.g = 255
    else if rgba.g < adjust
      rgba.g = 0
      
    if rgba.b > 255 - adjust
      rgba.b = 255
    else if rgba.b < adjust
      rgba.b = 0

    rgba

# ## Channels
# Lets you modify the intensity of any combination of red, green, or blue channels individually.
#
# ### Arguments
# Must be given at least one color channel to adjust in order to work.
# Options format (must specify 1 - 3 colors):
# <pre>{
#   red: 20,
#   green: -5,
#   blue: -40
# }</pre>
Filter.register "channels", (options) ->
  return @ if typeof options isnt "object"

  for own chan, value of options
    if value is 0
      delete options[chan]
      continue

    options[chan] /= 100

  return @ if options.length is 0

  @process "channels", (rgba) ->
    if options.red?
      if options.red > 0
        rgba.r += (255 - rgba.r) * options.red
      else
        rgba.r -= rgba.r * Math.abs(options.red)

    if options.green?
      if options.green > 0
        rgba.g += (255 - rgba.g) * options.green
      else
        rgba.g -= rgba.g * Math.abs(options.green)

    if options.blue?
      if options.blue > 0
        rgba.b += (255 - rgba.b) * options.blue
      else
        rgba.b -= rgba.b * Math.abs(options.blue)

    rgba

# ## Curves
# Curves implementation using Bezier curve equation. If you're familiar with the Curves 
# functionality in Photoshop, this works in a very similar fashion.
#
# ### Arguments.
# <pre>
#   chan - [r, g, b, rgb]
#   start - [x, y] (start of curve; 0 - 255)
#   ctrl1 - [x, y] (control point 1; 0 - 255)
#   ctrl2 - [x, y] (control point 2; 0 - 255)
#   end   - [x, y] (end of curve; 0 - 255)
# </pre>
#
# The first argument represents the channels you wish to modify with the filter. It can be an 
# array of channels or a string (for a single channel). The rest of the arguments are 2-element 
# arrays that represent point coordinates. They are specified in the same order as shown in this 
# image to the right. The coordinates are in the range of 0 to 255 for both X and Y values.
#
# The x-axis represents the input value for a single channel, while the y-axis represents the 
# output value.
Filter.register "curves", (chans, cps...) ->
  # If channels are in a string, split to an array
  chans = chans.split("") if typeof chans is "string"
  chans = ['r', 'g', 'b'] if chans[0] == "v"

  if cps.length < 3 or cps.length > 4
    # might want to give a warning now
    throw "Invalid number of arguments to curves filter"

  start = cps[0]
  ctrl1 = cps[1]
  ctrl2 = if cps.length == 4 then cps[2] else cps[1]
  end = cps[cps.length - 1]

  # Generate a bezier curve
  bezier = Calculate.bezier start, ctrl1, ctrl2, end, 0, 255

  # If the curve starts after x = 0, initialize it with a flat line
  # until the curve begins.
  bezier[i] = start[1] for i in [0...start[0]] if start[0] > 0

  # ... and the same with the end point
  bezier[i] = end[1] for i in [end[0]..255] if end[0] < 255

  @process "curves", (rgba) ->
    # Now that we have the bezier curve, we do a basic hashmap lookup
    # to find and replace color values.
    rgba[chans[i]] = bezier[rgba[chans[i]]] for i in [0...chans.length]
    rgba

# ## Exposure
# Adjusts the exposure of the image by using the curves function.
#
# ### Arguments
# Range is -100 to 100. Values < 0 will decrease exposure while values > 0 will increase exposure.
Filter.register "exposure", (adjust) ->
  p = Math.abs(adjust) / 100

  ctrl1 = [0, 255 * p]
  ctrl2 = [255 - (255 * p), 255]

  if adjust < 0
    ctrl1 = ctrl1.reverse()
    ctrl2 = ctrl2.reverse()

  @curves 'rgb', [0, 0], ctrl1, ctrl2, [255, 255]



# Allows us to crop the canvas and produce a new smaller
# canvas.
Caman.Plugin.register "crop", (width, height, x = 0, y = 0) ->
  # Create our new canvas element
  if exports?
    canvas = new Canvas width, height
  else
    canvas = document.createElement 'canvas'
    Util.copyAttributes @canvas, canvas

    canvas.width = width
    canvas.height = height

  ctx = canvas.getContext '2d'

  # Perform the cropping by drawing to the new canvas
  ctx.drawImage @canvas, x, y, width, height, 0, 0, width, height

  @cropCoordinates = x: x, y: y

  # Update all of the references
  @cropped = true
  @replaceCanvas canvas

# Resize the canvas and the image to a new size
Caman.Plugin.register "resize", (newDims = null) ->
  # Calculate new size
  if newDims is null or (!newDims.width? and !newDims.height?)
    Log.error "Invalid or missing dimensions given for resize"
    return

  if not newDims.width?
    # Calculate width
    newDims.width = @canvas.width * newDims.height / @canvas.height
  else if not newDims.height?
    # Calculate height
    newDims.height = @canvas.height * newDims.width / @canvas.width

  if exports?
    canvas = new Canvas newDims.width, newDims.height
  else
    canvas = document.createElement 'canvas'
    Util.copyAttributes @canvas, canvas

    canvas.width = newDims.width
    canvas.height = newDims.height

  ctx = canvas.getContext '2d'

  ctx.drawImage @canvas, 
    0, 0, 
    @canvas.width, @canvas.height, 
    0, 0, 
    newDims.width, newDims.height

  @resized = true
  @replaceCanvas canvas

Caman.Filter.register "crop", ->
  @processPlugin "crop", Array.prototype.slice.call(arguments, 0)

Caman.Filter.register "resize", ->
  @processPlugin "resize", Array.prototype.slice.call(arguments, 0)

###
IDMC plugins
###

# resetOriginalPixelData is broken, this is the way it should be

Caman.Filter.register "idmc_reset_original_pixeldata", () ->
  	@processPlugin "idmc_reset_original_pixeldata", null

Caman.Plugin.register "idmc_reset_original_pixeldata", () ->
	
	Log.debug "idmc_reset_original_pixeldata"

	@originalPixelData = Util.dataArray(@pixelData.length)
	@originalPixelData[i] = pixel for pixel, i in @pixelData
	@

# Adjust minimum and maximim pixel values

Caman.Filter.register "idmc_set_min_max_pixel_values", (min_pixel_value, max_pixel_value) ->
  @processPlugin "idmc_set_min_max_pixel_values", [min_pixel_value, max_pixel_value]


Caman.Plugin.register "idmc_set_min_max_pixel_values", (min_pixel_value, max_pixel_value) ->
	org_pixels = @originalPixelData	
	pixels = @pixelData
	width = @dimensions.width
	height = @dimensions.height

	if not @idmc_set_min_max_pixel_values_r_colormap?	
		@idmc_set_min_max_pixel_values_r_colormap = (i for i in [0...256])

	if not @idmc_set_min_max_pixel_values_g_colormap?	
		@idmc_set_min_max_pixel_values_g_colormap = (i for i in [0...256])

	if not @idmc_set_min_max_pixel_values_b_colormap?	
		@idmc_set_min_max_pixel_values_b_colormap = (i for i in [0...256])

	r_colormap = @idmc_set_min_max_pixel_values_r_colormap
	g_colormap = @idmc_set_min_max_pixel_values_g_colormap
	b_colormap = @idmc_set_min_max_pixel_values_b_colormap


	idx = (x,y) => (y*width + x) * 4

	for i in [0...256]
		#Log.debug "i: " +i+ ", " +min_pixel_value+ ", " + "max_pixel_value"


		index = Math.round((256 * (i - min_pixel_value)) / (max_pixel_value - min_pixel_value));
		#Log.debug "index1: " +index

		index = if index < 0
			0
		else if i > 255
			255
		else 
			index

		#Log.debug "index2: " +index		

		r_colormap[i] = if i < min_pixel_value
			0
		else if i > max_pixel_value
			255
		else
			index

		g_colormap[i] = if i < min_pixel_value
			0
		else if i > max_pixel_value
			255
		else
			index

		b_colormap[i] = if i < min_pixel_value
			0
		else if i > max_pixel_value
			255
		else 
			index


	for y in [0...height]
		for x in [0...width]
			#Log.debug "org_pixels[" +x+ "," +y+ "]: " + org_pixels[idx(x,y)]

			r = org_pixels[idx(x,y)]
			g = org_pixels[idx(x,y) + 1]
			b = org_pixels[idx(x,y) + 2]
			a = org_pixels[idx(x,y) + 3]
	
			pixels[idx(x,y)]     = r_colormap[r]
			pixels[idx(x,y) + 1] = g_colormap[g]
			pixels[idx(x,y) + 2] = b_colormap[b]
			pixels[idx(x,y) + 3] = 255	

	@

Caman.Filter.register "idmc_test", () ->
  	@processPlugin "idmc_test", []

Caman.Plugin.register "idmc_test", () ->
	@process "idmc_test", (rgba) ->
		Log.debug "IDMC test func"
		rgba
@

