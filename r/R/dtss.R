#' Open a shiny server for server-side DT::datatable visualization
#'
#' @param dt DT::Table
#'
#' @export
dtss <- function(dt) {
  ui <- shiny::fluidPage(
    # shiny::titlePanel("Edgar Anderson's Iris Data"),
    DT::dataTableOutput("dt")
  )

  server <- function(input, output, session) {
    session$onSessionEnded(function() {
      shiny::stopApp()
    })
    output$dt <- DT::renderDT({
      dt
    })
  }

  shiny::shinyApp(ui = ui, server = server)
}
