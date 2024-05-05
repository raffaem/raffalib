#' Convert a dataframe to DT::datatable for visualization
#'
#' @param df A dataframe
#' @param to_truncate Text columns too long that needs to be truncated
#' @param truncate_max An integer with maximum length of a string before it is truncated
#' @param truncate_max_title An integer representing the maximum length of the substring in tooltip
#' @param types_in_colnames A boolean equal to TRUE if datatypes should be appended to column names
#' @param filter Position of the filter widgets
#' @param to_round A character vector with numeric colum names that have to be rounded
#' @param to_round_digits Maximum number of digits for rounded columns
#' @param fixed_header Whether the header row should be fixed when scrolling
#' @param page_length Number of rows per page
#'
#' @return a DT::datatable
#'
#' @importFrom magrittr %>%
#'
#' @export
df2dt <- function(df,
                  to_truncate = "auto",
                  truncate_max = 20,
                  truncate_max_title = 200,
                  types_in_colnames = TRUE,
                  filter = "top",
                  to_round = "auto",
                  to_round_digits = 2,
                  fixed_header = TRUE,
                  page_length = 20) {
  # check that `df` is indeed a dataframe
  if (!("data.frame" %in% class(df))) {
    print("ERROR: df is not a data frame")
    return(NULL)
  }
  # Build column names string for display
  # Substitute "_" with spaces to allow long column names to return to new lines
  newcolnames <- colnames(df)
  for (i in seq(1, length(newcolnames))) {
    newcolnames[i] <- stringr::str_replace_all(newcolnames[i], "_", " ")
  }
  # Insert data type in column names
  if (types_in_colnames) {
    for (i in seq(1, length(colnames(df)))) {
      col <- colnames(df)[i]
      newcolnames[i] <- paste0(
        newcolnames[i],
        "\n{",
        class(df[[col]])[1],
        "}"
      )
    }
  }
  # Find in an automatic way which string columns
  # we need to truncate
  if (length(to_truncate) == 1 && to_truncate == "auto") {
    to_truncate <- c()
    for (col in colnames(df)) {
      if (class(df[[col]])[1] != "character") {
        next
      }
      # For a logical vector,
      # which.min returns the index of the first FALSE
      # as FALSE < TRUE
      ix <- which.min(is.na(df[[col]]))
      x <- df[[col]][ix]
      if (is.na(x)) {
        # The column is made entirely of NAs
        next
      }
      strl <- stringr::str_length(x)
      if (strl > truncate_max) {
        to_truncate <- c(to_truncate, col)
      }
    }
  }
  # Make sure all columns to truncate are of "character" class
  to_truncate_2 <- c()
  for (col in to_truncate) {
    if (class(df[[col]]) == "character") {
      to_truncate_2 <- c(to_truncate_2, col)
    } else {
      # print(paste0("Column ", col, " removed
      #          from columns to truncate
      #          because it isn't of character class"))
    }
  }
  to_truncate <- to_truncate_2
  cat("to_truncate=")
  print(paste0(to_truncate, collapse = ";"))
  cat("\n")
  # We need to replace NA values with a character value
  # for columns we are going to truncate,
  # otherwise DT crashes and show an empty table
  l <- list()
  for (col in to_truncate) {
    l[[col]] <- "NA"
  }
  df <- df %>% tidyr::replace_na(l)
  # Compute rows to round automatically
  if (length(to_round) == 1 && to_round == "auto") {
    to_round <- c()
    for (col in colnames(df)) {
      if (class(df[[col]])[1] == "numeric") {
        to_round <- c(to_round, col)
      }
    }
  }
  cat("to_round=")
  print(paste0(to_round, collapse = ";"))
  cat("\n")
  # Get column index to truncate for DT::datatable
  to_truncate_ix <- which(colnames(df) %in% to_truncate)
  # Options
  options <- list(
    pageLength = page_length,
    filter = "top",
    autoWidth = TRUE,
    columnDefs = list(
      # Truncate too long character columns
      list(
        targets = to_truncate_ix,
        render = DT::JS(
          "function(data, type, row, meta) {",
          "return type === 'display' && ",
          "data.length > ", truncate_max, " ?",
          "'<span title=\"' + ",
          "data.substr(0,", truncate_max_title, ") + ",
          "'...\">' + ",
          "data.substr(0, ", truncate_max, ") + ",
          "'...</span>' : data;",
          "}"
        )
      )
    )
  )
  # Extensions: fixed header
  extensions <- NULL
  if (fixed_header) {
    extensions <- "FixedHeader"
    options$fixedHeader <- TRUE
  }
  # Generate DT table
  dtobj <- DT::datatable(df,
    colnames = newcolnames,
    filter = filter,
    extensions = extensions,
    options = options
  )
  # Round number columns
  dtobj <- dtobj %>% DT::formatRound(to_round, to_round_digits)
  return(dtobj)
}
